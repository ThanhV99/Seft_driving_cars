from tkinter import *
import cv2
from PIL import Image,ImageTk
import numpy as np
import serial

arduino = serial.Serial('COM5', 9600)
tk = Tk()
tk.title("Machine Vision")
tk.geometry("1440x700+5+5")
tk.resizable(0,0)

cap = cv2.VideoCapture("https://192.168.43.1:8080/video") #1920x1080

canvas = Canvas(tk,width=1440, height=480)
canvas.place(x=0,y=0)

photo = None

curveList = []
avgVal = 10
result = False
char_stop = False
text_curve = 0
text_side = ""

label1 = Label(tk,text=str(text_curve),font="Courier 30")
label1.place(x=710,y=500)
label2 = Label(tk,text=str(text_side),font="Courier 30")
label2.place(x=690,y=550)

def empty():
    pass
def colorTrackbar(width=640,height=240):
    cv2.namedWindow("HSV")
    cv2.resizeWindow("HSV", width, height)
    cv2.createTrackbar("HUE Min", "HSV", 0, 179, empty)
    cv2.createTrackbar("HUE Max", "HSV", 179, 179, empty)
    cv2.createTrackbar("SAT Min", "HSV", 0, 255, empty)
    cv2.createTrackbar("SAT Max", "HSV", 255, 255, empty)
    cv2.createTrackbar("VALUE Min", "HSV", 0, 255, empty)
    cv2.createTrackbar("VALUE Max", "HSV", 255, 255, empty)

def thresholding(img):
    img_hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    h_min = cv2.getTrackbarPos("HUE Min", "HSV")
    h_max = cv2.getTrackbarPos("HUE Max", "HSV")
    s_min = cv2.getTrackbarPos("SAT Min", "HSV")
    s_max = cv2.getTrackbarPos("SAT Max", "HSV")
    v_min = cv2.getTrackbarPos("VALUE Min", "HSV")
    v_max = cv2.getTrackbarPos("VALUE Max", "HSV")
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    maskWhite = cv2.inRange(img_hsv, lower, upper)
    return maskWhite

def warpImg(img, points, w, h, inv=False):
    pts1 = np.float32(points)
    pts2 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    if inv:
        matrix = cv2.getPerspectiveTransform(pts2, pts1)
    else:
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgWarp = cv2.warpPerspective(img, matrix, (w, h))
    return imgWarp#anh kich co w,h

def nothing(a):
    pass

def initializeTrackbars(intialTracbarVals, wT=480, hT=240):
    cv2.namedWindow("Position")
    cv2.resizeWindow("Trackbars", 360, 240)
    cv2.createTrackbar("Width Top", "Position", intialTracbarVals[0], wT // 2, nothing)
    cv2.createTrackbar("Height Top", "Position", intialTracbarVals[1], hT, nothing)
    cv2.createTrackbar("Width Bottom", "Position", intialTracbarVals[2], wT // 2, nothing)
    cv2.createTrackbar("Height Bottom", "Position", intialTracbarVals[3], hT, nothing)

def valTrackbars(wT=480, hT=240):
    widthTop = cv2.getTrackbarPos("Width Top", "Position")
    heightTop = cv2.getTrackbarPos("Height Top", "Position")
    widthBottom = cv2.getTrackbarPos("Width Bottom", "Position")
    heightBottom = cv2.getTrackbarPos("Height Bottom", "Position")
    points = np.float32([(widthTop, heightTop), (wT - widthTop, heightTop),
                         (widthBottom, heightBottom), (wT - widthBottom, heightBottom)])
    return points

def drawPoints(img, points):
    for x in range(4):
        cv2.circle(img, (int(points[x][0]), int(points[x][1])), 15, (0, 0, 255), cv2.FILLED)
    return img

def getHistogram(img, minPer=0.1, display=False, region=1):
    if region == 1:
        histValues = np.sum(img, axis=0)#cong tong cac cot, mang gom width phan tu
    else:
        histValues = np.sum(img[img.shape[0] // region:, :], axis=0) #chia chieu height

    # print(histValues)
    maxValue = np.max(histValues) #gia tri max
    minValue = minPer * maxValue  #gia tri min = 0.5*max loc nhieu
                                  #0.9 gia tri min value cao-> chi con` 1 ben trai phai
    indexArray = np.where(histValues >= minValue) #chi so cac hang cua histvalue co gia tri lon hon min
    basePoint = int(np.average(indexArray))#cong tong indexarray/so phan tu = gia tri trung binh
    # print(basePoint)

    if display:
        imgHist = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)
        for x, intensity in enumerate(histValues):
            cv2.line(imgHist, (x, img.shape[0]), (x, img.shape[0] - intensity // 255 // region), (255, 0, 255), 1) #intensity//255 so pixel
            cv2.circle(imgHist, (basePoint, img.shape[0]), 20, (0, 255, 255), cv2.FILLED)#1 diem trung binh goc duoi
        return basePoint, imgHist
    return basePoint

def stackImages(imgArray):
    for i in range(len(imgArray)):
        if len(imgArray[i].shape) == 2:
            imgArray[i] = cv2.cvtColor(imgArray[i],cv2.COLOR_GRAY2BGR)
        imgArray[i] = cv2.cvtColor(imgArray[i], cv2.COLOR_BGR2RGB)
    imgstack1 = np.hstack((imgArray[0],imgArray[1],imgArray[2]))
    imgstack2 = np.hstack((imgArray[3],imgArray[4],imgArray[5]))
    result = np.vstack((imgstack1,imgstack2))
    return result

def getLaneCurve(img, display=2):
    imgCopy = img.copy()
    imgResult = img.copy()

    #### STEP 1

    imgThres = thresholding(img) #thu duoc anh den trang

    #### STEP 2
    hT, wT, c = img.shape #240x480x3
    points = valTrackbars() #lay toa do 4 diem
    imgWarp = warpImg(imgThres, points, wT, hT) #xoay anh
    imgWarpPoints = drawPoints(imgCopy, points) #ve 4 diem vao` anh imgCopy

    #### STEP 3
    middlePoint, imgHist1 = getHistogram(imgWarp, display=True, minPer=0.5, region=4) #do độ sáng gần góc dưới điểm cân bằng của biểu đồ sáng ở giữa, chia 4 phan lay' 3 phan duoi'
    curveAveragePoint, imgHist2 = getHistogram(imgWarp, display=True, minPer=0.9)#tra ve 1 diem thể hiện số lượng pixel nhiều ở bên trái hay phải
    curveRaw = curveAveragePoint - middlePoint #tru gia tri - la left, + la right

    #### STEP 4
    curveList.append(curveRaw) #gia tri tru them vao list
    if len(curveList) > avgVal: #10 gia tri xoa gia tri dau(lon hon 10 khung hinh)
        curveList.pop(0)
    curve = int(sum(curveList) / len(curveList))#gia tri trung binh cua list
    #### STEP 5
    if display != 0:
        imgInvWarp = warpImg(imgWarp, points, wT, hT, inv=True)
        imgInvWarp = cv2.cvtColor(imgInvWarp, cv2.COLOR_GRAY2BGR)
        imgInvWarp[0:hT // 3, 0:wT] = 0, 0, 0
        imgLaneColor = np.zeros_like(img)
        imgLaneColor[:] = 0, 255, 0
        imgLaneColor = cv2.bitwise_and(imgInvWarp, imgLaneColor)
        imgResult = cv2.addWeighted(imgResult, 1, imgLaneColor, 1, 0)
        cv2.putText(imgResult, str(curve), (wT // 2 - 80, 85), cv2.FONT_HERSHEY_COMPLEX, 2, (255, 0, 255), 3)
    if display == 2:
        imgStacked = stackImages([img, imgWarpPoints, imgWarp, imgHist2, imgLaneColor, imgResult])

    #NORMALIZATION
    curve = curve / 100
    if curve > 1: curve = 1
    if curve < -1: curve = -1
    return curve, imgStacked

intialTrackBarVals = [102, 80, 20, 214]
initializeTrackbars(intialTrackBarVals)
colorTrackbar(640,240)
def update_frame():
    global canvas,photo,bw,label1,text_curve
    success, img = cap.read()
    img = cv2.resize(img, (480, 240))
    curve,imgStacked=getLaneCurve(img, display=2)
    if curve <= -0.2:
        label2.configure(text="LEFT")
    elif curve > -0.2 and curve < 0.2:
        label2.configure(text="STRAIGHT")
    elif curve >= 0.2:
        label2.configure(text="RIGHT")
    label1.configure(text=str(int(curve*100)))
    if char_stop:
        arduino.write(b'q')
    if result:
        print(curve)
        if curve <= -0.2:
            arduino.write(b'0')
            print("LEFT")
        elif curve > -0.2 and curve < 0.2:
            arduino.write(b'1')
            print("STRAIGHT")
        elif curve >= 0.2:
            arduino.write(b'2')
            print("RIGHT")
    photo = ImageTk.PhotoImage(image=Image.fromarray(imgStacked))
    canvas.create_image(0,0,image=photo,anchor=NW)
    tk.after(3,update_frame)
update_frame()

def start():
    global result
    result = True
def stop():
    global result,char_stop
    result = False
    char_stop = True

button_start = Button(tk,text="START",command=start,padx=30,pady=10,bd=5)
button_start.place(x=500,y=620)
button_stop = Button(tk,text="STOP",command=stop,padx=30,pady=10,bd=5)
button_stop.place(x=1000,y=620)

tk.mainloop()