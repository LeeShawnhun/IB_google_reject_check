from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import pandas as pd
from datetime import date
import re

# 터미널에 uvicorn main:app --reload 로 실행
app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

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
    all_brand_data = []

    for file_path in file_paths:
        temp = pd.read_csv(
            file_path, 
            encoding="UTF-16",
            sep='\t',
            usecols=['광고 이름', '광고 유형', '캠페인', '광고 정책'],
            header=2)
        
        temp = temp[temp["광고 유형"] == "반응형 동영상 광고"]
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
            
            all_brand_data.append(f"{campaign}")
            all_brand_data.extend(reject_ads)
            all_brand_data.append("")

    output_file = f'{formatted_date} 구글 리젝 체크.txt'
    with open(output_file, 'w', encoding='utf-8') as file:
        for line in all_brand_data:
            file.write(f"{line}\n")
    
    return output_file

@app.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile] = File(...)):
    try:
        file_paths = []
        for file in files:
            file_path = file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(file_path)
        
        processed_file = process_files(file_paths)
        
        # Clean up uploaded files
        for file_path in file_paths:
            os.remove(file_path)
        
        download_link = f'/download/{processed_file}'
        return HTMLResponse(content=f"""
        <html>
            <body>
                <h1>처리가 완료되었습니다.</h1>
                <p>아래 버튼을 클릭하여 결과 파일을 다운로드하세요:</p>
                <a href="{download_link}" download>
                    <button>다운로드</button>
                </a>
            </body>
        </html>
        """)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename, media_type='text/plain', filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """
    <html>
        <head>
            <title>File Processor</title>
        </head>
        <body>
            <h1>Upload CSV Files</h1>
            <form action="/uploadfiles/" enctype="multipart/form-data" method="post">
                <input name="files" type="file" accept=".csv" multiple>
                <input type="submit" value="Upload and Process">
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)