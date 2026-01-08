####### quiz 1

# station = "사당"
# (station + "행 열차가 들어오고 있습니다.")

# station = "신도림"
# print(station + "행 열차가 들어오고 있습니다.")

# station = "인천공항"
# print(station + "행 열차가 들어오고 있습니다.")

####### quiz 2

# from random import *
# date = randint(4,28)
# print("오프라인 스터디 모임 날짜는 매월 " , date , "일로 선정되었습니다")

####### quiz 3

# homepage = "http://naver.com"
# site = homepage[7:homepage.index(".")] # replace 써서도 가능
# print(site[:3] + str(len(site)) + str(site.count("e")) + "!")

####### quiz 4

# from random import *

# users = range(1, 21) # 1 ~ 20까지 숫자를 생성
# users = list(users)
# shuffle(users)
# winners = sample(users,4) 
# print("-- 당첨자 발표 --")
# print("치킨 당첨자 : {0}".format(winners[0]), )
# print("커피 당첨자 : {0}".format(winners[1:]))
# print("-- 축하합니다 --")

####### quiz 5

# from random import *

# index = 0
# for i in range(1, 51):
#     spending_time = randrange(5, 51)
#     if spending_time >= 5 and spending_time <= 15:
#         print("[O] {0}번째 손님 (소요시간 : {1}분)".format(i,spending_time))
#         index += 1
#     else:
#         print("[ ] {0}번째 손님 (소요시간 : {1}분)".format(i,spending_time))

# print("\n 총 탑승 승객 : {0} 분".format(index))

####### quiz 6

# height = 175
# gender = "남자"

# def std_weight(height, gender):
#     if gender == "남자":
#         return height * height * 22
#     else:
#         return height * height * 21

# print("키 {0}cm {1}의 표준 체중은 {2}kg 입니다.".format(height, gender, round(std_weight(height / 100, gender),2)))

####### quiz 7

# for i in range(1, 51):
#     with open(str(i) + "주차.txt", "w", encoding="utf8") as file:
#         file.write("- {0} 주차 주간보고 -".format(i))
#         file.write("\n부서 :")
#         file.write("\n이름 :")
#         file.write("\n업무 요약 :")

####### quiz 8

# class House:
#     # 매물 초기화
#     def __init__(self, location, house_type, deal_type, price, completion_year):
#         self.location = location
#         self.house_type = house_type
#         self.deal_type = deal_type
#         self.price = price
#         self.completion_year = completion_year

#     # 매물 정보 표시
#     def show_detail(self):
#         print(self.location, self.house_type, self.deal_type, self.price, self.completion_year)
        
# apart = House("강남", "아파트", "매매", "10억", "2010년")
# opistel = House("마포", "오피스텔", "전세", "5억", "2007년")
# villa = House("송파", "빌라", "월세", "500/50억", "2000년")

# houses = [apart, opistel, villa]

# print("총 {0}대의 건물이 있습니다.".format(len(houses)))
# for house in houses:
#     house.show_detail()

####### quiz 9

# class SoldOutError(Exception):
#     pass
    
# chicken = 10
# waiting = 1
# while(True):
#     try:
#         print("[남은 치킨] : {0}".format(chicken))
#         order = int(input("치킨 몇 마리 주문하시겠습니까?"))
    
#         if order > chicken:
#             print("재료가 부족합니다.")
#         elif order < 1:
#             raise ValueError
#         else:
#             print("[대기번호 {0}] {1} 마리 주문이 완료되었습니다.".format(waiting, order))
#             waiting += 1
#             chicken -= order

#             if chicken == 0:
#                 raise SoldOutError
#     except ValueError:
#         print("잘못된 값을 입력하였습니다.")
#     except SoldOutError:
#         print("재고가 소진되어 더 이상 주문을 받지 않습니다.")
#         break

####### quiz 10

# import byme
# byme.sign()