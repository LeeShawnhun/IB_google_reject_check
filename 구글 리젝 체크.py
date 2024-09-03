import glob
import re
import pandas as pd
from datetime import date

today = date.today()
formatted_date = today.strftime("%m%d")

def reason_preprocessing(text):
    if "클릭베이트" in text:
        text = "클릭베이트"
        
    elif "일부 제한됨" in text:
        text = "일부 제한됨"
        
    elif "신뢰할 수 없는 주장" in text:
        text = "신뢰할 수 없는 주장"
        
    elif '개인 맞춤 광고 정책 내 건강 관련 콘텐츠 (제한됨)' in text:
        text = '개인 맞춤 광고 정책 내 건강 관련 콘텐츠'
        
    else:
        pattern = r"YouTube 광고 요건 - ([^(]+)(?:\([^)]*\))? \(제한됨\)"
        match = re.search(pattern, text)
        if match:
            text = match.group(1).strip()
    return text

reject_list = glob.glob("./테스트/*.csv")
all_brand_data = []

for brand in reject_list:
    temp = pd.read_csv(
        brand, 
        encoding="UTF-16",
        sep='\t',
        usecols=['광고 이름', '광고 유형', '캠페인', '광고 정책'],
        header=2)
    
    temp = temp[temp["광고 유형"] == "반응형 동영상 광고"]
    temp_campaign_name = temp["캠페인"].unique()
    
    for campaign in temp_campaign_name:
        temp_ad_by_campaign = temp[temp["캠페인"] == campaign]
        temp_list = []
        
        for index, row in temp_ad_by_campaign.iterrows():
            name = row['광고 이름']
            reasons = row['광고 정책'].split(";")
            reasons = [x for x in reasons if "(제한 없음)" not in x]
            reasons = [reason_preprocessing(reason) for reason in reasons]
            reasons = ", ".join(reasons)
            temp_list.append(f"{name}({reasons})")
            
        duplicate_check = pd.DataFrame(temp_list)
        reject_ads = duplicate_check[0].unique()
        
        all_brand_data.append(f"{campaign}")
        all_brand_data.extend(reject_ads)
        all_brand_data.append("")

with open(f'{formatted_date} 구글 리젝 체크.txt', 'w', encoding='utf-8') as file:
    for line in all_brand_data:
        file.write(f"{line}\n")