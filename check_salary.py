#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""연봉 계산 확인"""

# JSON 데이터
total_salary = 10665558000  # 연봉 총액
employees = 619  # 직원 수
jan_salary_am = 16956000  # JSON의 1인당 연봉

# 계산
per_person_calculated = total_salary / employees

print("=" * 60)
print("연봉 계산 확인")
print("=" * 60)
print(f"연봉 총액: {total_salary:,}원 ({total_salary/100000000:.2f}억원)")
print(f"직원 수: {employees}명")
print()
print(f"1인당 연봉 (총액/인원): {per_person_calculated:,.0f}원 = {per_person_calculated/10000:.0f}만원")
print(f"JSON의 jan_salary_am: {jan_salary_am:,}원 = {jan_salary_am/10000:.0f}만원")
print()
print(f"차이: {per_person_calculated - jan_salary_am:,.0f}원")
print()
print("=" * 60)
print("결론:")
print("=" * 60)
if abs(per_person_calculated - jan_salary_am) < 1000000:  # 100만원 이내 차이면 거의 같음
    print("JSON의 jan_salary_am 값이 맞습니다.")
    print(f"1인당 연봉: 약 {jan_salary_am/10000:.0f}만원")
else:
    print("JSON의 jan_salary_am 값과 계산값이 다릅니다.")
    print(f"계산값: 약 {per_person_calculated/10000:.0f}만원")
    print(f"JSON값: 약 {jan_salary_am/10000:.0f}만원")
    print("(jan_salary_am이 월급이거나 다른 의미일 수 있습니다)")










