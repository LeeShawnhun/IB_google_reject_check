from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import shutil
import os
import pandas as pd
from datetime import date
import re
import traceback
from sqlalchemy.orm import Session
from database import get_db, engine 
import models

# 터미널에 uvicorn main:app --reload 로 실행
app = FastAPI()

# 정적 파일 서빙 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# db 테이블 초기화
models.Base.metadata.create_all(bind=engine)

def save_to_database(db: Session, processed_data):
    today = date.today()
    for campaign, ads in processed_data.items():
        for ad in ads:
            name, reasons = ad.split('(', 1)
            reasons = reasons.rstrip(')')
            db_item = models.RejectedAd(
                date=today,
                campaign=campaign,
                ad_name=name,
                reasons=reasons
            )
            db.add(db_item)
    db.commit()

team_brands = {
    "team1": ['비아벨로', '라이브포레스트', '겟비너스', '본투비맨', '마스터벤', '안마디온', '다트너스', '뮤끄', '프렌냥'],
    "team2A": ['해피토리', '뉴티365', '디다', '아비토랩'],
    "team2B": ['씨퓨리', '리베니프', '리디에뜨', '에르보떼'],
    "team3": ['하아르', '리서쳐스', '리프비기닝', '리서쳐스포우먼', '아르다오'],
    "team4": ['베다이트', '데이배리어', '리프비기닝', '건강도감', '리서쳐스포우먼']
}

def reason_preprocessing(text):
    if "클릭베이트" in text:
        return "클릭베이트"
    elif "일부 제한됨" in text:
        return "일부 제한됨"
    elif "신뢰할 수 없는 주장" in text:
        return "신뢰할 수 없는 주장"
    elif '개인 맞춤 광고 정책 내 건강 관련 콘텐츠 (제한됨)' in text:
        return '개인 맞춤 광고 정책 내 건강 관련 콘텐츠'
    else:
        pattern = r"YouTube 광고 요건 - ([^(]+)(?:\([^)]*\))? \(제한됨\)"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return text

def process_files(file_paths):
    today = date.today()
    formatted_date = today.strftime("%m%d")
    processed_data = {}

    for file_path in file_paths:
        temp = pd.read_csv(
            file_path, 
            encoding="UTF-16",
            sep='\t',
            usecols=['광고 이름', '광고 유형', '캠페인', '승인 상태','광고 정책'],
            header=2)
        
        temp = temp[(temp["광고 유형"] == "반응형 동영상 광고") & (temp["승인 상태"] != "승인됨")]
        temp_campaign_name = temp["캠페인"].unique()
        
        for campaign in temp_campaign_name:
            temp_ad_by_campaign = temp[temp["캠페인"] == campaign]
            temp_list = []
            
            for _, row in temp_ad_by_campaign.iterrows():
                name = row['광고 이름']
                reasons = row['광고 정책'].split(";")
                reasons = [x for x in reasons if "(제한 없음)" not in x]
                reasons = [reason_preprocessing(reason) for reason in reasons]
                reasons = ", ".join(reasons)
                temp_list.append(f"{name}({reasons})")
                
            duplicate_check = pd.DataFrame(temp_list)
            reject_ads = duplicate_check[0].unique()
            
            processed_data[campaign] = reject_ads

    output_file = f'{formatted_date} 구글 리젝 체크.txt'

    with open(output_file, 'w', encoding='utf-8') as file:
        for campaign, ads in processed_data.items():
            file.write(f"{campaign}\n")
            for ad in ads:
                file.write(f"{ad}\n")
            file.write("\n")
    
    return processed_data, output_file

@app.post("/uploadfiles/")
async def create_upload_files(request: Request, files: list[UploadFile] = File(...), selected_team: str = Form(...), db: Session = Depends(get_db)):
    try:
        file_paths = []
        for file in files:
            file_path = os.path.join("temp", file.filename)  # 'temp' 디렉토리에 파일 저장
            os.makedirs("temp", exist_ok=True)  # 'temp' 디렉토리가 없으면 생성
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(file_path)
        
        # 선택된 팀의 브랜드 순서 가져오기
        team_brands_list = team_brands.get(selected_team, [])
        
        # 파일 경로를 브랜드 순서에 따라 정렬
        sorted_file_paths = []
        for brand in team_brands_list:
            for file_path in file_paths:
                if f"_{brand}.csv" in file_path:
                    sorted_file_paths.append(file_path)
                    break
        
        # 정렬된 파일 경로로 처리
        processed_data, output_file = process_files(sorted_file_paths)
        
        # 데이터베이스에 저장
        save_to_database(db, processed_data)
        
        for file_path in file_paths:
            os.remove(file_path)
        
        download_link = f'/download/{output_file}'
        return templates.TemplateResponse("result.html", {"request": request, "download_link": download_link})
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename, media_type='text/plain', filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/check_data/", response_class=HTMLResponse)
def check_data(request: Request, db: Session = Depends(get_db)):
    results = db.query(models.RejectedAd).all()
    return templates.TemplateResponse("check_data.html", {"request": request, "results": results})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)