# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 14:20:52 2024

@author: user
"""

import pandas as pd 
from tqdm import tqdm
from glob import glob
import seaborn as sns
import scipy.stats as stats
from scipy.stats import norm
from scipy.stats import shapiro
import matplotlib.pyplot as plt
from scipy.stats import kstest

path = r'C:\Users\user\Desktop\유동균\99. 데이터\전월세전환율/'

df = pd.read_excel(path + '규모별 전월세 전환율_아파트.xlsx', skipfooter = 2)

df = pd.read_excel(path + '규모별 전월세 전환율_연립_다세대.xlsx', skipfooter = 2)



df.loc[df['그룹'] == '서울', '그룹'] = df.loc[df['그룹'] == '서울', '그룹'] + ' ' + df.loc[df['그룹'] == '서울', '그룹.1']
df.drop([0], axis = 0, inplace = True)
df.drop(['No', '그룹.1'], axis = 1, inplace = True)
df.insert(0, '주택유형', '연립다세대')
df.set_index(['주택유형', '그룹', '분류'], inplace = True)

def jws_ratio_applied_jeonse(housing_type, area, location, month, deposit, rent, ratio_df) : 
    
    month1 = month[:4] + '년 ' + month[4:].lstrip('0') + '월' 
    
    if '서울' in location : 
        if location.split(' ')[-1] in ['종로구', '중구', '용산구'] : 
            loc_cat = '서울 도심권'
        elif location.split(' ')[-1] in ['성동구', '광진구', '동대문구', '중랑구', '성북구', '강북구','도봉구', '노원구'] : 
            loc_cat = '서울 동북권'
        elif location.split(' ')[-1] in ['은평구', '서대문구', '마포구'] : 
            loc_cat = '서울 서북권'
        elif location.split(' ')[-1] in ['양천구', '강서구', '구로구', '금천구', '영등포구', '동작구', '관악구'] : 
            loc_cat = '서울 서남권'
        elif location.split(' ')[-1] in ['서초구', '강남구', '송파구', '강동구'] : 
            loc_cat = '서울 동남권'
    else : 
        loc_cat = location
    
    if housing_type == '연립다세대' : 
        if area <= 30 :
            area_cat = '30㎡이하'
        elif area > 30 and area <= 60 :
            area_cat = '30㎡초과 60㎡이하'
        if area > 60 :
            area_cat = '60㎡초과'
            
    elif housing_type == '아파트' :
        if area <= 60 :
            area_cat = '60㎡이하'
        elif area > 60 and area <= 85 :
            area_cat = '60㎡초과 85㎡이하'
        elif area > 85 : 
            area_cat = '85㎡초과'
      
    ratio = ratio_df.loc[(housing_type, loc_cat, area_cat), month1]
    
    rent = rent * 10000
    deposit = deposit * 10000
    
    jeonse_price = (12*rent*100)/ratio + deposit
    
    print('\n' + '예상되는 전세 가격은 ' + f"{int(jeonse_price):,}" + ' 원 입니다.' )
    print('계산식에 사용된 전월세 전환율은 ' + month1 + ' 기준 ' + str(ratio) + '% 입니다.')    
            
            
            

jws_ratio_applied_jeonse('연립다세대', 85, '서울 양천구', '202411', 20000, 50, df)
        
#%%

# 표제부
path = r'C:\Users\user\Desktop\유동균\99. 데이터\건축물대장/'
col_path = r'C:\Users\user\Desktop\유동균\0. Before\MyDataBank\유동균\공공데이터\건축물대장\내가 정리한 것/'

col = pd.read_excel(col_path + '건축물대장 컬럼명 정리.xlsx')

pjb = pd.read_parquet(path + '0_pjb.parquet')
pjb.columns = col['표제부'][1:]

# 서울시 아파트 202407 ~ 202412 실거래
path = r'C:\Users\user\Desktop\유동균\99. 데이터\전월세전환율/'

file_list = glob(path + '*실거래가*.csv')

df = pd.concat([pd.read_csv(k, sep = ',', encoding = 'cp949', dtype = str) for k in file_list], axis = 0, ignore_index = True)
df['주소'] = df['시군구'] + ' ' + df['번지']
df = df[df['시군구'].str.startswith('서울특별시')]

lgst = df['주소'].value_counts().reset_index()

# 케이스 데이터 확인
case = df[df['주소'] == '서울특별시 송파구 가락동 913']
case['전용면적(㎡)'] = case['전용면적(㎡)'].astype(float)

area_bins = [0, 60, 85, 1000]
case['area_cat'] = pd.cut(case['전용면적(㎡)'], area_bins, labels = ['60㎡이하', '60㎡초과 85㎡이하', '85㎡초과'], right = True)

case['area_cat'].value_counts()

case1 = case[case['area_cat'] == '60㎡초과 85㎡이하']

#%% 전세
case11 = case1[case1['전월세구분'] == '전세']
case11['보증금(만원)'] = case11['보증금(만원)'].astype(int)

# 히스토그램
sns.histplot(case11['보증금(만원)'], kde=True, bins=30, color='blue')
plt.title("Histogram with KDE")
plt.show()

# Q-Q 플롯
stats.probplot(case11['보증금(만원)'], dist="norm", plot=plt)
plt.title("Q-Q Plot")
plt.show()

# 샤피로-윌크 검정
stat, p = shapiro(case11['보증금(만원)'])
print(f"Shapiro-Wilk Test Statistic: {stat}, p-value: {p}")

if p > 0.05:
    print("데이터가 정규 분포를 따릅니다. (귀무가설 채택)")
else:
    print("데이터가 정규 분포를 따르지 않습니다. (귀무가설 기각)")

# 콜모고로프-스미르노프 검정
stat, p = kstest(case11['보증금(만원)'], 'norm', args=(case11['보증금(만원)'].mean(), case11['보증금(만원)'].std()))
print(f"Kolmogorov-Smirnov Test Statistic: {stat}, p-value: {p}")

if p > 0.05:
    print("데이터가 정규 분포를 따릅니다. (귀무가설 채택)")
else:
    print("데이터가 정규 분포를 따르지 않습니다. (귀무가설 기각)")

# 이상치 제거
# IQR 계산
Q1 = case11['보증금(만원)'].quantile(0.25)
Q3 = case11['보증금(만원)'].quantile(0.75)
IQR = Q3 - Q1

# 이상치 조건
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# 이상치 제거
case12 = case11[(case11['보증금(만원)'] >= lower_bound) & (case11['보증금(만원)'] <= upper_bound)]

# 이상치 제거 전 전세 보증금 평균
f"{case11['보증금(만원)'].mean().round(2) * 10000:,.0f}"
# 이상치 제거 후 전세 보증금 평균
f"{case12['보증금(만원)'].mean().round(2) * 10000:,.0f}"


f"{case11['보증금(만원)'].median() * 10000:,.0f}"

#%% 월세

case13 = case1[case1['전월세구분'] == '월세']
case13['보증금(만원)'] = case13['보증금(만원)'].astype(int)
case13['월세금(만원)'] = case13['월세금(만원)'].astype(int)

# 히스토그램
sns.histplot(case13['보증금(만원)'], kde=True, bins=30, color='blue')
plt.title("Histogram with KDE")
plt.show()

# Q-Q 플롯
stats.probplot(case13['보증금(만원)'], dist="norm", plot=plt)
plt.title("Q-Q Plot")
plt.show()

# 샤피로-윌크 검정
stat, p = shapiro(case13['보증금(만원)'])
print(f"Shapiro-Wilk Test Statistic: {stat}, p-value: {p}")

if p > 0.05:
    print("데이터가 정규 분포를 따릅니다. (귀무가설 채택)")
else:
    print("데이터가 정규 분포를 따르지 않습니다. (귀무가설 기각)")

# 콜모고로프-스미르노프 검정
stat, p = kstest(case13['보증금(만원)'], 'norm', args=(case13['보증금(만원)'].mean(), case13['보증금(만원)'].std()))
print(f"Kolmogorov-Smirnov Test Statistic: {stat}, p-value: {p}")

if p > 0.05:
    print("데이터가 정규 분포를 따릅니다. (귀무가설 채택)")
else:
    print("데이터가 정규 분포를 따르지 않습니다. (귀무가설 기각)")

# 이상치 제거
# IQR 계산
Q1 = case13['보증금(만원)'].quantile(0.25)
Q3 = case13['보증금(만원)'].quantile(0.75)
IQR = Q3 - Q1

# 이상치 조건
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# 이상치 제거
case131 = case13[(case13['보증금(만원)'] >= lower_bound) & (case13['보증금(만원)'] <= upper_bound)]

# 이상치 제거 후 월세 보증금 평균
f"{case131['보증금(만원)'].mean().round(2) * 10000:,.0f}"
# 보증금 중위값
f"{case131['보증금(만원)'].median() * 10000:,.0f}"

# 월세금
# 이상치 제거
# IQR 계산
Q1 = case13['월세금(만원)'].quantile(0.25)
Q3 = case13['월세금(만원)'].quantile(0.75)
IQR = Q3 - Q1

# 이상치 조건
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# 이상치 제거
case132 = case13[(case13['월세금(만원)'] >= lower_bound) & (case13['월세금(만원)'] <= upper_bound)]

# 이상치 제거 후 전세 월세 평균
f"{case131['월세금(만원)'].mean().round(2) * 10000:,.0f}"
# 보증금 중위값
f"{case131['월세금(만원)'].median() * 10000:,.0f}"

헬리오시티 60 < 전용면적 <= 85

전세 보증금 평균 : 1,017,542,200
월세 보증금 평균 : 459777800
월세 평균 : 2293100

a = 1029639800
b = 459777800
c = 2293100

c * 12 / (a - b) * 100

헬리오시티 60㎡초과 85㎡이하 전월세전환율 : 4.83 %
rone 규모별(60㎡초과 85㎡이하) 전월세전환율(11월 기준) : 4.6 %
rone 송파구 전월세전환율(11월 기준) : 4.3 %

rent = 2870000
deposit = 200000000
ratio = 4.83
ratio1 = 4.6
ratio2 = 4.3



(12*rent*100)/ratio + deposit # 913,043,478 원

(12*rent*100)/ratio1 + deposit # 948,695,652 원

(12*rent*100)/ratio2 + deposit # 1,000,930,232 원



# 중위값으로 계산(이상치 제거 X)

a = 1050000000
b = 420000000
c = 2200000

c * 12 / (a - b) * 100

이상치 제거 안한 데이터의 중위값 : 4.19 %

#%% 초안

# 서울시 아파트 202407 ~ 202412 실거래
path = r'C:\Users\user\Desktop\유동균\99. 데이터\전월세전환율/'

file_list = glob(path + '*실거래가*.csv')

df = pd.concat([pd.read_csv(k, sep = ',', encoding = 'cp949', dtype = str) for k in file_list], axis = 0, ignore_index = True)
df['주소'] = df['시군구'] + ' ' + df['번지'] + ' ' + df['단지명']
df = df[df['시군구'].str.startswith('서울특별시')].reset_index(drop = True)

df['전용면적(㎡)'] = df['전용면적(㎡)'].astype(float)
df['보증금(만원)'] = df['보증금(만원)'].astype(int)
df['월세금(만원)'] = df['월세금(만원)'].astype(int)

# 케이스 데이터 확인

apt = '서울특별시 중랑구 면목동 1077-1 용마한신'
a = '60㎡초과 85㎡이하'

addr = list(df['주소'].unique())

ratio_df_list = []

for i in tqdm(range(len(addr))) : 
    apt = addr[i]
    
    case = df[df['주소'] == apt]
    
    area_bins = [0, 60, 85, 1000]
    case['area_cat'] = pd.cut(case['전용면적(㎡)'], area_bins, labels = ['60㎡이하', '60㎡초과 85㎡이하', '85㎡초과'], right = True)

    ratio_dict = {}

    for a in list(case['area_cat'].unique()) : 
        
        case1 = case[case['area_cat'] == a]
        
        # 평균 전세보증금, 월세보증금, 월세 구하기
        case2 = case1[case1['전월세구분'] == '전세']
        case21 = case1[case1['전월세구분'] == '월세']

        j_cnt = len(case2)
        w_cnt = len(case21)

        # 이상치 제거
        # IQR 계산
        Q1 = case2['보증금(만원)'].quantile(0.25)
        Q11 = case21['보증금(만원)'].quantile(0.25)
        
        Q3 = case2['보증금(만원)'].quantile(0.75)
        Q31 = case21['보증금(만원)'].quantile(0.75)
        
        IQR = Q3 - Q1
        IQR1 = Q31 - Q11

        # 이상치 조건
        lower_bound = Q1 - 1.5 * IQR
        lower_bound1 = Q11 - 1.5 * IQR1
        
        upper_bound = Q3 + 1.5 * IQR
        upper_bound1 = Q31 + 1.5 * IQR1
        
        # 이상치 제거
        case3 = case2[(case2['보증금(만원)'] >= lower_bound) & (case2['보증금(만원)'] <= upper_bound)]
        case31 = case21[(case21['보증금(만원)'] >= lower_bound1) & (case21['보증금(만원)'] <= upper_bound1)]
        
        # 평균 전세보증금
        depo = round(case3['보증금(만원)'].mean() * 10000, 0)
        rent_depo = round(case31['보증금(만원)'].mean() * 10000, 0)
        rent = round(case31['월세금(만원)'].mean() * 10000, 0)

        ratio = round(rent * 12 / (depo - rent_depo) * 100, 2)

        ratio_dict[a] = ratio
        ratio_dict[a + ' / 전세표본수'] = j_cnt
        ratio_dict[a + ' / 월세표본수'] = w_cnt

    ratio_dict['apt'] = apt

    rdf = pd.DataFrame.from_dict({key : [value] for key, value in ratio_dict.items()})
    ratio_df_list.append(rdf)

final_ratio_df = pd.concat(ratio_df_list, axis = 0)

condition = (((final_ratio_df['60㎡초과 85㎡이하 / 전세표본수'] >= 10) & (final_ratio_df['60㎡초과 85㎡이하 / 월세표본수'] >= 10)) |
            ((final_ratio_df['60㎡이하 / 전세표본수'] >= 10) & (final_ratio_df['60㎡이하 / 월세표본수'] >= 10)) |
            ((final_ratio_df['85㎡초과 / 전세표본수'] >= 10) & (final_ratio_df['85㎡초과 / 월세표본수'] >= 10)))

final = final_ratio_df[condition]
final = final[['apt', '60㎡이하', '60㎡초과 85㎡이하', '85㎡초과']]
















