# coding= utf-8
import os
from keras.utils import np_utils
import matplotlib.pyplot as plt
import cv2
from keras.models import Sequential, load_model
from keras.layers import Dense, Activation, Convolution2D, MaxPooling2D, Flatten, Dropout, BatchNormalization
import numpy as np
from keras.callbacks import TensorBoard
from itertools import cycle
from sklearn.metrics import roc_curve, auc
from scipy import interp

#根据输入的文件夹绝对路径，将该文件夹下的所有指定后缀的文件读取存入一个list,该list的第一个元素是该文件夹的名字
def readAllImg(path,*suffix):
    try:

        s = os.listdir(path)
        resultArray = []

        for i in s:
            if endwith(i, suffix):
                document = os.path.join(path, i)
                # 读取文件
                img = cv2.imread(document)
                resultArray.append(img)


    except IOError:
        print ("Error")

    else:
        print ("读取成功")
        return resultArray

#输入一个字符串一个标签，对这个字符串的后续和标签进行匹配
def endwith(s,*endstring):
   resultArray = map(s.endswith,endstring)
   if True in resultArray:
       return True
   else:
       return False

# 输入一个文件路径，对其下的每个文件夹下的图片读取，并对每个文件夹给一个不同的Label
# 返回一个img的list,返回一个对应label的list,返回一下有几个文件夹（有几种label)

def read_file(path):
    img_list = []
    label_list = []
    dir_counter = 0

    n = 0
    # 对路径下的所有子文件夹中的所有jpg文件进行读取并存入到一个list中
    for child_dir in os.listdir(path):
        child_path = os.path.join(path, child_dir)

        for dir_image in os.listdir(child_path):
            # print(child_path)
            if endwith(dir_image, 'jpg'):
                img = cv2.imread(os.path.join(child_path, dir_image))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # print(n)
                img_list.append(img)
                label_list.append(dir_counter)
                n = n + 1

        dir_counter += 1

    # 返回的img_list转成了 np.array的格式
    img_list = np.array(img_list)

    return img_list, label_list, dir_counter


# 读取训练数据集的文件夹，把他们的名字返回给一个list
def read_name_list(path):
    name_list = []
    for child_dir in os.listdir(path):
        name_list.append(child_dir)
    return name_list


# 建立一个用于存储和格式化读取训练数据的类
class DataSet(object):
    def __init__(self, path1, path2):
        self.num_classes = None
        self.X_train = None
        self.X_test = None
        self.Y_train = None
        self.Y_test = None
        self.extract_data(path1, path2)
        # 在这个类初始化的过程中读取path下的训练数据

    def extract_data(self, path1, path2):
        # 根据指定路径读取出图片、标签和类别数
        X_test, y_test, counter2 = read_file(path2)
        X_train, y_train, counter1 = read_file(path1)

        X_train = X_train.reshape(X_train.shape[0], 128, 128, 1)
        X_test = X_test.reshape(X_test.shape[0], 128, 128, 1)
        X_train = X_train.astype('float32') / 255
        X_test = X_test.astype('float32') / 255
        # 将labels转成 binary class matrices
        Y_train = np_utils.to_categorical(y_train, num_classes=counter1)
        Y_test = np_utils.to_categorical(y_test, num_classes=counter2)

        # 将格式化后的数据赋值给类的属性上
        self.X_train = X_train
        self.X_test = X_test
        self.Y_train = Y_train
        self.Y_test = Y_test
        self.num_classes = counter1

    def check(self):
        print('num of dim:', self.X_test.ndim)
        print('shape:', self.X_test.shape)
        print('size:', self.X_test.size)

        print('num of dim:', self.X_train.ndim)
        print('shape:', self.X_train.shape)
        print('size:', self.X_train.size)



# 建立一个基于CNN的识别模型
class Model(object):
    FILE_PATH = r"./model/model1.h5"  # 模型进行存储和读取的地方

    def __init__(self):
        self.model = None

    # 读取实例化后的DataSet类作为进行训练的数据源
    def read_trainData(self, dataset):
        self.dataset = dataset

    # 建立一个CNN模型，一层卷积、一层池化、一层卷积、一层池化、抹平之后进行全链接、最后进行分类  其中flatten是将多维输入一维化的函数 dense是全连接层
    def build_model(self):
        self.model = Sequential()
        # 卷积层
        self.model = Sequential()
        self.model.add(
            Convolution2D(filters=20,
                          kernel_size=(5, 5),
                          padding='same',
                          input_shape=self.dataset.X_train.shape[1:],

                          )
        )
        self.model.add(BatchNormalization())

        self.model.add(Activation('relu'))
        self.model.add(MaxPooling2D(pool_size=(2, 2),strides=(2, 2),padding='same')
        )

        self.model.add(Convolution2D(filters=64, kernel_size=(5, 5), padding='same'))
        self.model.add(BatchNormalization())
        self.model.add(Activation('relu'))
        self.model.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2), padding='same'))
        self.model.add(Dropout(0.15))

        self.model.add(Flatten())
        self.model.add(Dense(512))
        self.model.add(BatchNormalization())
        self.model.add(Activation('relu'))
        self.model.add(Dropout(0.5))

        self.model.add(Dense(128))
        self.model.add(BatchNormalization())
        self.model.add(Activation('relu'))
        self.model.add(Dropout(0.5))

        self.model.add(Dense(self.dataset.num_classes))
        self.model.add(BatchNormalization())
        self.model.add(Activation('softmax'))
        self.model.summary()

    # 进行模型训练的函数，具体的optimizer、loss可以进行不同选择
    def train_model(self):
        self.model.compile(
            optimizer='adadelta',
            loss='categorical_crossentropy',
            metrics=['accuracy'])

        # epochs、batch_size为可调的参数，epochs为训练多少轮、batch_size为每次训练多少个样本
        self.model.fit(self.dataset.X_train, self.dataset.Y_train, epochs=3, batch_size=20,
                       callbacks=[TensorBoard(log_dir=r'./log')])
     # callbacks=[TensorBoard(log_dir=r'E:/classification/log')表示准确率与loss曲线存在的位置，

    def evaluate_model(self):
        print('\nTesting---------------')
        loss, accuracy = self.model.evaluate(self.dataset.X_test, self.dataset.Y_test)
        from sklearn.metrics import confusion_matrix
        print(np.argmax(self.dataset.Y_test,axis=1))
        print(np.argmax(self.model.predict_proba(self.dataset.X_test), axis=1))
        conf = confusion_matrix(np.argmax(self.dataset.Y_test,axis=1), np.argmax(self.model.predict_proba(self.dataset.X_test), axis=1))
        total_correct = 0.
        nb_classes = conf.shape[0]
        for i in np.arange(0, nb_classes):
            total_correct += conf[i][i]
        acc = total_correct / sum(sum(conf))
        print('分类准确率 = %.4f' % acc)

    def save(self, file_path=FILE_PATH):
        print('Model Saved.')
        self.model.save(file_path)

    def load(self, file_path=FILE_PATH):
        print('Model Loaded.')
        self.model = load_model(file_path)


    def predict(self, img):
        img = img.reshape((1, 128, 128, 1))
        img = img.astype('float32')
        img = img / 255.0
        result = self.model.predict_proba(img)  # 测算一下该img属于某个label的概率
        max_index = np.argmax(result)  # 找出概率最高的

        return max_index, result[0][max_index]  # 第一个参数为概率最高的label的index,第二个参数为对应概率

    def ROC(self):
        n_classes = 2
        # 计算每一类的ROC
        fpr = dict()
        tpr = dict()
        y_score = self.model.predict_proba(self.dataset.X_test)
        roc_auc = dict()
        for i in range(n_classes):
            fpr[i], tpr[i], _ = roc_curve(self.dataset.Y_test[:,i], y_score[:,i])
            roc_auc[i] = auc(fpr[i], tpr[i])

        all_fpr = np.unique(np.concatenate([fpr[i] for i in range(n_classes)]))
        mean_tpr = np.zeros_like(all_fpr)
        for i in range(n_classes):
            mean_tpr += interp(all_fpr, fpr[i], tpr[i])
        mean_tpr /= n_classes
        fpr["macro"] = all_fpr
        tpr["macro"] = mean_tpr
        roc_auc["macro"] = auc(fpr["macro"], tpr["macro"])

        # Plot all ROC curves
        lw = 1
        plt.figure()


        colors = cycle(['aqua', 'darkorange', 'cornflowerblue'])
        for i, color in zip(range(n_classes), colors):
            plt.rcParams['font.sans-serif'] = ['SimSun']
            plt.plot(fpr[i], tpr[i], color=color, lw=lw,
                     label=u'第{0}类的ROC曲线 (AUC = {1:0.2f})'
                           ''.format(i, roc_auc[i]))


        plt.plot([0, 1], [0, 1], 'k--', lw=lw)
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.rcParams['font.sans-serif'] = ['SimSun']
        plt.xlabel(u"假正例率")
        plt.ylabel(u"真正例率")
        plt.legend(loc="lower right")
        plt.show()

if __name__ == '__main__':
    datast = DataSet(r"./dataset/train\\",r"./dataset/test\\")
    model = Model()
    model.read_trainData(datast)
    model.build_model()
    model.train_model()
    # model.load()
    model.evaluate_model()
    model.save()
    """模型保存，下次再运行可注释掉
    model.build_model()
    model.train_model()
    这两行，然后将model.load()取消注释即可"""
    model.ROC()
