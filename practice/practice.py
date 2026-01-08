# print(5)
# print(3.14)
# print(not (5<10))

#################### 자료형 ######################

# # 애완동물을 소개해 주세요~
# name = "연탄이"
# animal = "강아지"
# age = 4
# hobby = "산책"
# is_adult = age <= 3

# print("우리집 " + animal + "의 이름은 " + name + "에요")
# print(name, "는 " + str(age) + "살이며, " + hobby + "을 아주 좋아해요")
# print("연탄이는 어른일까요? " + str(is_adult))

# print(name, "는 ", age , "살이며, " , hobby , "을 아주 좋아해요")

###################### 연산자 ######################

# print(1+1) # 2
# print(3-2) # 1
# print(5*2) # 10
# print(6/3) # 2
# print(2**3) # 2^3 = 8
# print(5%3) # 나머지 구하기, 2
# print(5//3) # 몫 구하기, 1
# print(10 > 3) # True
# print(4 >= 7) # False
# print(5 <= 5) # True
# print(3 == 3) # True
# print(4 == 2) # False
# print(1 != 3) # True
# print(not(1 != 3)) # False
# print((3 > 0 ) and (3 < 5)) # True
# print((3 > 0 ) & (3 < 5)) # True
# print((3 > 0 ) or (3 > 5)) # True
# print((3 > 0 ) | (3 > 5)) # True
# print(5 > 4 > 3) # True
# print(5 > 4 > 7) # False

##################### 수식 ########################

# number = 2 + 3 * 4 # 14
# print(number)
# number += 2 # 16
# print(number)
# number *= 2 # 32
# print(number)
# number /= 2 # 16
# print(number)
# number -= 2 # 14
# print(number)
# number %= 5 #4
# print(number)

################## 숫자 처리 함수 ###################
# print(abs(-5)) # 절대값, 5
# print(pow(4, 2)) # pow(a,b) = a^b, 4^2 = 16
# print(max(5, 12)) # 더 큰 값, 12
# print(round(3.14)) # 반올림, 3
# print(round(4.99)) # 반올림, 5

# from math import *
# print(floor(4.99)) # 내림, 4
# print(ceil(3.14)) # 올림, 4
# print(sqrt(16)) # 제곱근, 4

################### 난수 함수 ######################

# from random import *

# print(random()) # 0.0 ~ 1.0 미만의 임의의 값 생성
# print(random() * 10) # 0.0 ~ 10.0 미만의 임의의 값 생성
# print(int(random() * 10)) # 0 ~ 10 미만의 임의의 값 생성
# print(int(random() * 10) + 1) # 1 ~ 10 이하의 임의의 값 생성
# print(int(random() * 45) + 1) # 1 ~ 45 이하의 임의의 값 생성
# print(randrange(1, 46)) # 1 ~ 46 미만의 임의의 값 생성
# print(randint(1, 45)) # 1~ 45 이하의 임의의 값 생성

##################### 문자열 #######################

# sentence = '나는 소년입니다'
# print(sentence)
# sentence2 = "파이썬은 쉬워요"
# print(sentence2)
# sentence3 = """나는 소년이고, 파이썬은 쉬워요"""
# print(sentence3)

##################### 슬라이싱 ######################

# jumin = "990120-1234567"

# print("성별 : " + jumin[7]) # 1
# print("연 : " + jumin[0:2]) # 0 부터 2 직전까지(0,1), 99
# print("연 : " + jumin[2:4]) # 2 부터 4 직전까지(2,3), 01
# print("일 : " + jumin[4:6]) # 4 부터 6 직전까지(4,5), 20
# print("생년월일 : " + jumin[:6]) # 처음부터 6 직전까지, 990120
# print("뒤 7자리 : " + jumin[7:]) # 7 부터 끝까지, 1234567
# print("뒤 7자리(뒤에서부터) : " + jumin[-7:]) # 맨 뒤에서부터 7번째부터 끝까지, 1234567

################ 문자열 처리 함수 ####################

# python = "Python is Amazing"
# # print(python.lower()) # 모두 소문자로
# # print(python.upper()) # 모두 대문자로
# # print(python[0].isupper()) # 해당 문자가 대문자면 true 반환
# # print(len(python)) # 문자열 길이
# # print(python.replace("Python", "Java")) # 왼쪽 문자열을 오른쪽 문자열로 변환

# index = python.index("n") # 첫 번째 n의 위치
# print(index)
# index = python.index("n", index + 1) # 두 번째 n의 위치
# print(index)
# index = python.index("n", index + 1) # 세 번째 n의 위치
# print(index)
# print(python.find("Java")) # find 함수에서는 찾는 값이 없으면 -1 반환
# print(python.index("Java")) # index 함수에서는 찾는 값이 없으면 디버깅 오류
# print(python.count("n")) # python 문자열에서 n이 몇 번 나오는지

#################### 문자열 포멧 #######################

# # 방법 1
# print("나는 %d살입니다." % 20)
# print("나는 %s을 좋아해요." % "파이썬")
# print("Apple은 %c로 시작해요." % "A")
# print("나는 %s살입니다." % 20)
# print("나는 %s색과 %s색을 좋아해요." % ("파란","빨간"))

# # 방법 2
# print("나는 {}살입니다." .format(20))
# print("나는 {}색과 {}색을 좋아해요." .format("파란", "빨간"))
# print("나는 {0}색과 {1}색을 좋아해요." .format("파란", "빨간"))
# print("나는 {1}색과 {0}색을 좋아해요." .format("파란", "빨간"))

# # 방법 3
# print("나는 {age}살이며, {color}색을 좋아해요." .format(age = 20, color="빨간"))
# print("나는 {age}살이며, {color}색을 좋아해요." .format(color ="빨간", age = 20))

# # 방법 4 (v3.6 이상)
# age = 20
# color = "빨간"
# print(f"나는 {age}살이며, {color}색을 좋아해요.")

####################### 탈출 문자 ##########################

# print("백문이 불여일견 \n백견이 불여일타")

# # 저는 "나도코딩"입니다.
# print('저는 "나도코딩"입니다.')
# print("저는 \"나도코딩\"입니다.")

# # \\ : 문장 내에서 \
# print("C:\\Users\\Hoyoung\\Desktop\\PythonWorkspace>")

# # \r : 커서를 맨 앞으로 이동
# print("Red Apple\rPine")

# # \b : 백스페이스 (한 글자 삭제)
# print("Redd\bApple")

# # \t : 탭
# print("Red\tApple")

############################### 리스트 #############################

# # 지하철 칸 별로 10명, 20명, 30명
# subway = [10, 20 ,30]
# print(subway)

# subway = ["유재석", "조세호", "박명수"]
# print(subway)

# # 조세호씨가 몇 번째 칸에 타고 있는가?
# print(subway.index("조세호"))

# # 하하씨가 다음 정류장에서 다음 칸에 탐
# subway.append("하하")
# print(subway)

# # 정형돈씨를 유재석 / 조세호 사이에 태워봄
# subway.insert(1, "정형돈")
# print(subway)

# # 지하철에 있는 사람을 한 명씩 뒤에서 꺼냄
# print(subway.pop())
# print(subway)

# print(subway.pop())
# print(subway)

# print(subway.pop())
# print(subway)

# # 같은 이름의 사람이 몇 명 있는지 확인
# subway.append("유재석")
# print(subway)
# print(subway.count("유재석"))

# # 정렬도 가능
# num_list = [5,2,4,3,1]
# num_list.sort()
# print(num_list)

# # 뒤집기도 가능
# num_list.reverse()
# print(num_list)

# # 모두 지우기
# num_list.clear()
# print(num_list)

# # 다양한 자료형 함께 사용
# mix_list = ["조세호", 20, True]

# 리스트 확장
# num_list = [5,2,4,3,1]
# num_list.extend(mix_list)
# print(num_list)

############################# 사전 #############################

# cabinet = {3:"유재석", 100:"김태호"}
# print(cabinet[3])
# print(cabinet[100])
# print(cabinet.get(3))
# print(cabinet[5]) # 키에 해당하는 값이 없으면 즉시 프로그램 종료
# print(cabinet.get(5)) # 키에 해당하는 값이 없으면 None을 출력 후 다음 문장 실행
# print(cabinet.get(5, "사용 가능")) # 키에 해당하는 값이 없으면 "사용 가능" 출력
# print(3 in cabinet) # True
# print(5 in cabinet) # False

# cabinet = {"A-3":"유재석", "B-100":"김태호"}

# 새 손님
# print(cabinet)
# cabinet["A-3"] = "김종국"
# cabinet["C-20"] = "조세호"
# print(cabinet)

# # 간 손님
# del cabinet["A-3"]
# print(cabinet)

# # key들만 출력
# print(cabinet.keys())

# # value들만 출력
# print(cabinet.values())

# # key, value 쌍으로 출력
# print(cabinet.items())

# # 목욕탕 폐점
# cabinet.clear()
# print(cabinet)

########################## 튜플 #########################

# 튜플 -> 값 변경 불가, 속도가 빠름 => 변경되지 않는 자료를 쓸 때 유용

# menu = ("돈까스", "치즈까스")
# print(menu[0])
# print(menu[1])

# (name, age, hobby) = ("김종국", 20, "코딩")
# print(name, age, hobby)

####################### 세트 #########################

# 집합 (set)
# 중복 안됨, 순서 없음
# my_set = {1,2,3,3,3}
# print(my_set)

# java = {"유재석", "김태호", "양세형"}
# python = set(["유재석", "박명수"])

# # 교집합 (java와 python을 모두 할 수 있는 개발자)
# print(java & python)
# print(java.intersection(python))

# # 합집합 (java를 할 수 있거나 python을 할 수 있는 개발자)
# print(java | python)
# print(java.union(python))

# # 차집합 (java를 할 수 있지만 python은 할 줄 모르는 개발자)
# print(java - python)
# print(java.difference(python))

# # python을 할 줄 아는 사람이 늘어남
# python.add("김태호")
# print(python)

# #java를 잊었어요
# java.remove("김태호")
# print(java)

######################### 자료구조의 변경 #########################

# # 커피숍
# menu = {"커피", "우유", "주스"}
# print(menu, type(menu))

# menu = list(menu)
# print(menu, type(menu))

# menu = tuple(menu)
# print(menu, type(menu))

# menu = set(menu)
# print(menu, type(menu))

########################### if ##########################

# weather = input("오늘 날씨는 어때요? ")
# if weather == "비" or weather == "눈":
#     print("우산을 챙기세요")
# elif weather == "미세먼지":
#     print("마스크를 챙기세요")
# else:
#     print("준비물 필요 없어요")

# temp = int(input("기온은 어때요? "))
# if 30 <= temp:
#     print("너무 더워요. 나가지 마세요")
# elif 10 <= temp and temp < 30:
#     print("괜찮은 날씨에요")
# elif 0 <= temp < 10:
#     print("외투를 챙기세요")
# else:
#     print("너무 추워요. 나가지 마세요")

############################# for ###############################

# for waiting_num in range(1, 6): # 1, 2, 3, 4, 5
#     print("대기번호 : {0}".format(waiting_num))

# starbucks = ["아이언맨", "토르", "아이엠 그루트"]
# for customer in starbucks:
#     print("{0}, 커피가 준비되었습니다".format(customer))

########################### while ########################

# customer = "토르"
# index = 5
# while index >= 1:
#     print("{0}, 커피가 준비되었습니다. {1}번 남았어요".format(customer, index))
#     index -= 1
#     if index == 0:
#         print("커피는 폐기처분되었습니다")

# customer = "아이언맨"
# index = 1
# while True:
#     print("{0}, 커피가 준비되었습니다. 호출 {1}회".format(customer, index))
#     index += 1

# customer = "토르"
# person = "Unknown"

# while person != customer:
#     print("{0}, 커피가 준비 되었습니다".format(customer))
#     person = input("이름이 어떻게 되세요? ")

####################### continue와 break ##########################

# absent = [2, 5] # 결석
# no_book = [7] # 책을 깜빡했음
# for student in range(1, 11): # 1 ~ 10
#     if student in absent:
#         continue
#     elif student in no_book:
#         print("오늘 수업 여기까지. {0}는 교무실로 따라와".format(student))
#         break
#     print("{0}, 책을 읽어봐".format(student))

###################### 한 줄 for ########################

# # 출석 번호가 1 2 3 4, 앞에 100을 붙이기로 함 -> 101, 102, 103, 104
# students = [1, 2, 3, 4, 5]
# students = [i + 100 for i in students]
# print(students)

# # 학생 이름을 길이로 변환
# students = ["Iron man", "Thor", "I am groot"]
# students = [len(i) for i in students]
# print(students)

# # 학생 이름을 대문자로 변환
# students = ["Iron man", "Thor", "I am groot"]
# students = [i.upper() for i in students]
# print(students)

############################## 함수 ############################

# def open_account():
#     print("새로운 계좌가 생성되었습니다.")

# open_account()

########################### 전달값과 반환값 #######################

# def deposit(balance, money): # 입금
#     print("입금이 완료되었습니다. 잔액은 {0}원입니다.".format(balance + money))
#     return balance + money

# def withdraw(balance, money):
#     if balance >= money:
#         print("출금이 완료되었습니다. 잔액은 {0}원입니다.".format(balance - money))
#         return balance - money
#     else:
#         print("출금이 완료되지 않았습니다. 잔액은 {0}원입니다.".format(balance))
#         return balance

# def withdraw_night(balance, money):
#     commission = 100
#     return commission, balance - money - commission

# balance = 0
# balance = deposit(balance, 1000)
# print(balance)
# balance = withdraw(balance, 500)
# commission, balance = withdraw_night(balance, 500)
# print("수수료는 {0}원이며, 잔액은 {1}원입니다.".format(commission, balance))

###################### 기본값 ########################

# def profile(name, age, main_lang):
#     print("이름 : {0}\t나이 : {1}\t주 사용 언어: {2}".format(name, age, main_lang))

# profile("유재석", 20, "파이썬")
# profile("김태호", 25, "자바")

# 같은 학교 같은 학년 같은 반 같은 수업

# def profile(name, age = 17, main_lang = "파이썬"):
#     print("이름 : {0}\t나이 : {1}\t주 사용 언어: {2}".format(name, age, main_lang))

# profile("유재석")
# profile("김태호")

############################ 키워드 값 ##########################

# def profile(name, age, main_lang):
#     print(name, age, main_lang)

# profile(name="유재석", main_lang="파이썬", age="20")
# profile(main_lang="자바", age=25, name="김태호")

####################### 가변 인자 ##########################

# def profile(name, age, lang1, lang2, lang3, lang4, lang5):
#     print("이름 : {0},\t나이: {1}\t".format(name, age), end=" ") # end=" " : 문장을 출력한 후 줄 바꿈을 하지 않음
#     print(lang1, lang2, lang3, lang4, lang5)

# profile("유재석", 20, "Python", "Java", "C", "C++", "C#")
# profile("김태호", 25, "Kotlin", "Swift", "", "", "")

# def profile(name, age, *language):
#     print("이름 : {0},\t나이: {1}\t".format(name, age), end=" ")
#     for lang in language:
#         print(lang, end=" ")
#     print()
    
# profile("유재석", 20, "Python", "Java", "C", "C++", "C#", "JavaScript")
# profile("김태호", 25, "Kotlin", "Swift")

#################### 지역 변수, 전역 변수 ######################

# gun = 10

# def checkpoint(soldiers): # 경계근무
#     global gun # 전역 공간에 있는 gun 사용
#     gun = gun - soldiers
#     print("[함수 내] 남은 총 : {0}".format(gun))

# def checkpoint_ret(gun, soldiers):
#     gun = gun - soldiers
#     print("[함수 내] 남은 총 : {0}".format(gun))
#     return gun

# print("전체 총 : {0}".format(gun))
# checkpoint(2)
# gun = checkpoint_ret(gun, 2)
# print("남은 총 : {0}".format(gun))

######################## 표준 입출력 ###########################

# import sys

# print("Python", "Java", "JavaScript", sep=",", end ="?")
# print("무엇이 더 재밌을까요?")
# print("Python", "Java", file=sys.stdout)
# print("Python", "Java", file=sys.stderr)

# scores = {"수학" : 0, "영어" : 50, "코딩" : 100}
# for subject, score in scores.items():
#     # print(subject, score)
#     print(subject.ljust(8), str(score).rjust(4), sep=":") # ljust : 왼쪽 정렬, rjust : 오른쪽 정렬

# 은행 대기 순번표(001, 002, 003....)
# for num in range(1, 21):
#     print("대기번호 : " + str(num).zfill(3)) # zfill(n) : n칸만큼 공간을 확보하고 빈공간에 대해서는 0을 넣음

# answer = input("아무 값이나 입력하세요 : ") # 항상 문자열 형태로 저장됨
# print(type(answer))
# print("입력하신 값은" + answer + "입니다.")

######################## 다양한 출력 포맷 ##########################

# # 빈 자리는 빈 공간으로 두고, 오른쪽 정렬을 하되, 총 10자리 공간을 확보
# print("{0: > 10}".format(500))
# # 양수일 땐 +로 표시, 음수일 땐 -로 표시
# print("{0: >+10}".format(500))
# print("{0: >+10}".format(-500))
# # 왼쪽 정렬하고, 빈칸을 _로 채움
# print("{0:_<+10}".format(500))
# # 3자리 마다 콤마를 찍어주기
# print("{0:,}".format(100000000000))
# # 3자리 마다 콤마를 찍어주기, +- 부호도 붙이기
# print("{0:+,}".format(100000000000))
# print("{0:+,}".format(-100000000000))
# # 3자리 마다 콤마를 찍어주기, 부호도 붙이고, 자릿 수 확보하기
# # 돈이 많으면 행복하니까 빈 자리는 ^ 로 채워주기
# print("{0:^<+30,}".format(100000000000))
# print("{0:f}".format(5/3))
# # 소수점 특정 자리수 까지만 표시(소수점 3째 자리에서 반올림)
# print("{0:.2f}".format(5/3))

##################### 파일 입출력 ###########################

# score_file = open("score.txt", "w", encoding="utf8") # 쓰기 전용으로 열기(덮어씀)
# print("수학 : 0", file = score_file)
# print("영어 : 50", file = score_file)
# score_file.close()

# score_file = open("score.txt", "a", encoding="utf8") # 이어서 쓰기(a => appending)
# score_file.write("과학 : 80")
# score_file.write("\n코딩 : 100")
# score_file.close()

# score_file = open("score.txt", "r", encoding="utf8")
# print(score_file.read())
# score_file.close()

# score_file = open("score.txt", "r", encoding="utf8")
# print(score_file.readline(), end="") # 줄 별로 읽기, 한 줄 읽고 커서는 다음 줄로 이동
# print(score_file.readline(), end="") 
# print(score_file.readline(), end="") 
# print(score_file.readline(), end="") 
# score_file.close()

# score_file = open("score.txt", "r", encoding="utf8")
# while True:
#     line = score_file.readline()
#     if not line:
#         break
#     print(line, end="")
# score_file.close()

# score_file = open("score.txt", "r", encoding="utf8")
# lines = score_file.readlines() # list 형태로 저장
# for line in lines:
#     print(line, end="")
# score_file.close()

###################### pickle #######################

# import pickle
# profile_file = open("profile.pickle", "wb")
# profile = {"이름":"박명수", "나이":30, "취미":["축구","골프","코딩"]}
# print(profile)
# pickle.dump(profile, profile_file) # profile에 있는 정보를 file에 저장
# profile_file.close()

# profile_file = open("profile.pickle", "rb")
# profile = pickle.load(profile_file) # file에 있는 정보를 profile에 불러오기
# print(profile)
# profile_file.close()

##################### with ######################

# import pickle
# with open("profile.pickle", "rb") as profile_file:
#     print(pickle.load(profile_file))

# with open("study.txt", "w", encoding="utf8") as study_file:
#     study_file.write("파이썬을 열심히 공부하고 있어요")

# with open("study.txt", "r", encoding="utf8") as study_file:
#     print(study_file.read())

##################### 클래스, __init__, 멤버 변수 ########################

# class Unit:
#     def __init__(self, name, hp, damage): # __init__ : 생성자, 객체 : 클래스로부터 생성되는 것
#         self.name = name # 멤버 변수
#         self.hp = hp # 멤버 변수
#         self.damage = damage # 멤버 변수
#         print("{0} 유닛이 생성 되었습니다.".format(self.name))
#         print("체력 {0}, 공격력 {1}".format(self.hp, self.damage))

# marine1 = Unit("마린", 40, 5)
# marine2 = Unit("마린", 40, 5)
# tank = Unit("탱크", 150, 35) # 마린,탱크 : Unit 클래스의 인스턴스

# # 레이스 : 공중 유닛, 비행기, 클로킹 (상대방에게 보이지 않음)
# wraith1 = Unit("레이스", 80, 5)
# print("유닛 이름 : {0}, 공격력 : {1}".format(wraith1.name, wraith1.damage))

# # 마인드 컨트롤 : 상대방 유닛을 내 것으로 만드는 것
# wraith2 = Unit("빼앗은 레이스", 80, 5)
# wraith2.clocking = True

# if wraith2.clocking == True:
#     print("{0} 는 현재 클로킹 상태입니다.".format(wraith2.name))

#################### 메소드 #####################

# class Unit:
#     def __init__(self, name, hp, damage):
#         self.name = name 
#         self.hp = hp 
#         self.damage = damage 
#         print("{0} 유닛이 생성 되었습니다.".format(self.name))
#         print("체력 {0}, 공격력 {1}".format(self.hp, self.damage))

# class AttackUnit:
#     def __init__(self, name, hp, damage):
#         self.name = name 
#         self.hp = hp 
#         self.damage = damage

#     def attack(self, location):
#         print("{0} : {1} 방향으로 적군을 공격합니다. [공격력 {2}]".format(self.name, location, self.damage))

#     def damaged(self, damage):
#         print("{0} : {1} 데미지를 입었습니다.".format(self.name, damage))
#         self.hp -= damage
#         print("{0} : 현재 체력은 {1} 입니다.".format(self.name, self.hp))
#         if self.hp <= 0:
#             print("{0} : 파괴되었습니다.".format(self.name))

# # 파이어뱃 : 공격 유닛, 화염방사기
# firebat1 = AttackUnit("파이어뱃", 50 ,16)
# firebat1.attack("5시")

# # 공격 2번 받는다고 가정
# firebat1.damaged(25)
# firebat1.damaged(25)

####################### 상속(스타크래프트 프로젝트) ############################

# from random import *

# # 일반 유닛
# class Unit:
#     def __init__(self, name, hp, speed):
#         self.name = name 
#         self.hp = hp 
#         self.speed = speed
#         print("{0} 유닛이 생성되었습니다.".format(name))

#     def move(self, location):
#         print("{0} : {1} 방향으로 이동합니다. [속도 {2}]".format(self.name, location, self.speed)) 

#     def damaged(self, damage):
#         print("{0} : {1} 데미지를 입었습니다.".format(self.name, damage))
#         self.hp -= damage
#         print("{0} : 현재 체력은 {1} 입니다.".format(self.name, self.hp))
#         if self.hp <= 0:
#             print("{0} : 파괴되었습니다.".format(self.name))

# # 공격 유닛
# class AttackUnit(Unit):
#     def __init__(self, name, hp, speed, damage):
#         Unit.__init__(self, name, hp, speed) 
#         self.damage = damage

#     def attack(self, location):
#         print("{0} : {1} 방향으로 적군을 공격합니다. [공격력 {2}]".format(self.name, location, self.damage))

# class Marine(AttackUnit):
#     def __init__(self):
#         AttackUnit.__init__(self, "마린", 40, 1, 5)
    
#     # 스팀팩
#     def stimpack(self):
#         if self.hp > 10:
#             self.hp -= 10
#             print("{0} : 스팀팩을 사용합니다. (HP 10 감소)".format(self.name))
#         else:
#             print("{0} : 체력이 부족하여 스팀팩을 사용하지 않습니다.".format(self.name))

# # 탱크
# class Tank(AttackUnit):
#     # 시즈모드
#     seize_developed = False # 시즈모드 개발여부

#     def __init__(self):
#         AttackUnit.__init__(self, "탱크", 150, 1, 35)
#         self.seize_mode = False

#     def set_seize_mode(self):
#         if Tank.seize_developed == False:
#             return
        
#         # 현재 시즈모드가 아닐 때 -> 시즈모드
#         if self.seize_mode == False:
#             print("{0} : 시즈모드로 전환합니다.".format(self.name))
#             self.damage *= 2
#             self.seize_mode = True
#         # 현재 시즈모드일 때 -> 시즈모드 해제        
#         else:
#             print("{0} : 시즈모드를 해제합니다.".format(self.name))
#             self.damage /= 2
#             self.seize_mode = False

# # 파이어뱃 : 공격 유닛, 화염방사기
# firebat1 = AttackUnit("파이어뱃", 50 ,16)
# firebat1.attack("5시")

# # 공격 2번 받는다고 가정
# firebat1.damaged(25)
# firebat1.damaged(25)

######################## 다중 상속 ##########################

# # 날 수 있는 기능을 가진 클래스
# class Flyable:
#     def __init__(self, flying_speed):
#         self.flying_speed = flying_speed

#     def fly(self, name, location):
#         print("{0} : {1} 방향으로 날아갑니다. [속도 {2}]".format(name, location, self.flying_speed))
    
# # 공중 공격 유닛 클래스
# class FlyableAttackUnit(AttackUnit, Flyable):
#     def __init__(self, name, hp, damage, flying_speed):
#         AttackUnit.__init__(self, name, hp, 0, damage) # 지상 speed 0
#         Flyable.__init__(self, flying_speed)
    
#     def move(self, location):
#         self.fly(self.name, location)

# class Wraith(FlyableAttackUnit):
#     def __init__(self):
#         FlyableAttackUnit.__init__(self, "레이스", 80, 20, 5)
#         self.clocked = False # 클로킹 모드 (해제 상태)

#     def clocking(self):
#         if self.clocked == True: # 클로킹 모드 -> 모드 해제
#             print("{0} : 클로킹 모드를 해제합니다.".format(self.name))
#             self.clocked = False
#         else: # 클로킹 모드 해제 -> 모드 설정
#             print("{0} : 클로킹 모드를 설정합니다.".format(self.name))
#             self.clocked = True

# def game_start():
#     print("[알림] 새로운 게임을 시작합니다.")

# def game_over():
#     print("Player : gg")
#     print("[Player] 님이 게임에서 퇴장하셨습니다.")

# # 발키리
# valkyrie = FlyableAttackUnit("발키리", 200, 6, 5)
# valkyrie.fly(valkyrie.name, "3시")

#################### 메소드 오버라이딩 ########################

# # 벌쳐
# vulture = AttackUnit("벌쳐", 80, 10, 20)

# # 배틀크루저
# battlecruiser = FlyableAttackUnit("배틑크루저", 500, 25, 3)

# vulture.move("11시")
# battlecruiser.fly(battlecruiser.name, "9시")
# battlecruiser.move("9시")

#################### pass ######################

# # 건물
# class BuildingUnit(Unit):
#     def __init__(self, name, hp, location):
#         # Unit.__init__(self, name, hp, 0)
#         super().__init__(name, hp, 0)
#         self.location = location

# # 서플라이 디폿
# supply_depot = BuildingUnit("서플라이 디폿", 500, "7시")

# def game_start():
#     print("[알림] 새로운 겡미을 시작합니다.")

# def game_over():
#     pass

######################## super #########################

# class Unit:
#     def __init__(self):
#         print("Unit 생성자")

# class Flyable:
#     def __init__(self):
#         print("Flyable 생성자")   

# class FlyableUnit(Unit, Flyable):
#     def __init__(self):
#         #super().__init__() # 맨 처음 상속 받는 부모 클래스만 호출
#         Unit.__init__(self)
#         Flyable.__init__(self)

# # 드랍쉽
# dropship = FlyableUnit()

# # 게임 시작
# game_start()

# # 마린 3기 생성
# m1 = Marine()
# m2 = Marine()
# m3 = Marine()

# # 탱크 2기 생성
# t1 = Tank()
# t2 = Tank()

# # 레이스 1기 생성
# w1 = Wraith()

# # 유닛 일괄 관리
# attack_units = []
# attack_units.append(m1)
# attack_units.append(m2)
# attack_units.append(m3)
# attack_units.append(t1)
# attack_units.append(t2)
# attack_units.append(w1)

# # 전군 이동
# for unit in attack_units:
#     unit.move("1시")

# # 탱크 시즈모드 개발
# Tank.seize_developed = True
# print("[알림] 탱크 시즈 모드 개발이 완료되었습니다.")

# # 공격 모드 준비(마린 : 스팀팩, 탱크 : 시즈모드, 레이스 : 클로킹)
# for unit in attack_units:
#     if isinstance(unit, Marine):
#         unit.stimpack()
#     elif isinstance(unit, Tank):
#         unit.set_seize_mode()
#     elif isinstance(unit, Wraith):
#         unit.clocking()

# # 전군 공격
# for unit in attack_units:
#     unit.attack("1시")

# # 전군 피해
# for unit in attack_units:
#     unit.damaged(randint(5, 20)) # 공격은 랜덤으로 받음 (5 ~ 20)

# # 게임 종료
# game_over()

########################### 에외 처리 ###########################

# try:
#     print("나누기 전용 계산기입니다.")
#     nums = []
#     nums.append(int(input("첫 번째 숫자를 입력하세요 : ")))
#     nums.append(int(input("두 번째 숫자를 입력하세요 : ")))
#     # nums.append(int(nums[0]/nums[1]))
#     print("{0} / {1} = {2}".format(nums[0], nums[1], nums[2]))
# except ValueError:
#     print("에러! 잘못된 값을 입력하였습니다.")
# except ZeroDivisionError as err:
#     print(err)
# except Exception as err:
#     print("알 수 없는 에러가 발생하였습니다.")
#     print(err)

############################ 에러 발생시키기, 사용자 정의 예외처리, finally ############################

# class BigNumberError(Exception):
#     def __init__(self, msg):  # 안에서 아무것도 하지 않을 때는 pass(퀴즈 9 참고)
#         self.msg = msg

#     def __str__(self):
#         return self.msg

# try:
#     print("한 자리 숫자 나누기 전용 계산기입니다.")
#     num1 = int(input("첫 번째 숫자를 입력하세요 : "))
#     num2 = int(input("두 번째 숫자를 입력하세요 : ")) 
#     if num1 >= 10 or num2 >= 10:
#         raise BigNumberError("입력값 : {0}, {1}".format(num1, num2))
#     print("{0} / {1} = {2}".format(num1, num2, int(num1/num2)))
# except ValueError:
#     print("잘못된 값을 입력하였습니다. 한 자리 숫자만 입력하세요.")
# except BigNumberError as err:
#     print("에러가 발생하였습니다. 한 자리 숫자만 입력하세요.")
#     print(err)
# finally:
#     print("계산기를 이용해 주셔서 감사합니다.")

################################## 모듈 #################################

# import theater_module
# theater_module.price(3) # 3명이서 영화 보러 갔을 때 가격
# theater_module.price_morning(4) # 4명이서 조조 할인 영화 보러 갔을 때 가격
# theater_module.price_soldier(5) # 5명의 군인이 영화 보러 갔을 때 가격

# import theater_module as mv
# mv.price(3)
# mv.price_morning(4)
# mv.price_soldier(5)

# from theater_module import *
# price(3)
# price_morning(4)
# price_soldier(5)

# from theater_module import price, price_morning
# price(5)
# price_morning(6)
# #price_soldier(7) # X

# from theater_module import price_soldier as price
# price(5)

############################## 패키지, __all__, 패키지/모듈 위치 ##############################

# import travel.thailand
# #import travel.thailand.ThailandPackage # X
# trip_to = travel.thailand.ThailandPackage()
# trip_to.detail()

# from travel.thailand import ThailandPackage
# trip_to = ThailandPackage()
# trip_to.detail()

# from travel import vietnam
# trip_to = vietnam.VietnamPackage()
# trip_to.detail()

# from travel import *
# trip_to = vietnam.VietnamPackage()
# trip_to = thailand.ThailandPackage()
# trip_to.detail()

# import inspect
# import random
# print(inspect.getfile(random)) # random 모듈의 위치를 알려줌
# print(inspect.getfile(thailand))

######################## pip install ##########################

# # pypi : 패키지 목록을 볼 수 있는 사이트
# # pip list -> 설치되어 있는 패키지 리스트를 볼 수 있음
# # pip show 패키지명 -> 패키지의 정보를 알려줌
# # pip install --upgrade 패키지명 -> 패키지 업그레이드
# # pip uninstall 패키지명

# from bs4 import BeautifulSoup
# soup = BeautifulSoup("<p>Some<b>bad<i>HTML")
# print(soup.prettify())

####################### 내장 함수 #########################

# # list of built-in function : 내장 함수 목록을 볼 수 있는 사이트
# # input : 사용자 입력을 받는 함수
# language = input("무슨 언어를 좋아하세요?")
# print("{0}은 아주 좋은 언어입니다!".format(language))

# # dir : 어떤 객체를 넘겨줬을 때 그 객체가 어떤 변수와 함수를 가지고 있는지 표시
# print(dir())
# import random # 외장 함수
# print(dir())
# import pickle
# print(dir())
# print(dir(random))

# lst = [1, 2, 3]
# print(dir(lst))

# name = "Jim"
# print(dir(name))

############################# 외장 함수 ###########################

# # list of python modules : 외장 함수 목록을 볼 수 있는 사이트
# # glob : 경로 내의 폴더 / 파일 목록 조회 (윈도우 dir)
# import glob
# print(glob.glob("*.py")) # 확장자가 py 인 모든 파일

# # os : 운영채제에서 제공하는 기본 기능
# import os
# print(os.getcwd()) # 현재 디렉토리

# folder = "sample_dir"

# if os.path.exists(folder):
#     print("이미 존재하는 폴더입니다.")
#     os.rmdir(folder)
#     print(folder, "폴더를 삭제하였습니다.")
# else:
#     os.makedirs(folder) # 폴더 생성
#     print(folder, "폴더를 생성하였습니다.")
# print(os.listdir())

# # time : 시간 관련 함수
# import time
# print(time.localtime())
# print(time.strftime("%Y-%m-%d %H:%M:%S"))

# import datetime
# print("오늘 날짜는 ", datetime.date.today())

# # timedelta : 두 날짜 사이의 간격
# today = datetime.date.today() # 오늘 날짜 저장
# td = datetime.timedelta(days=100) # 100일 저장
# print("우리가 만난지 100일은", today + td) # 오늘부터 100일 후