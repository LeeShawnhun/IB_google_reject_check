const teamBrands = {
    team1: ['비아벨로', '라이브포레스트', '겟비너스', '본투비맨', '마스터벤', '안마디온', '다트너스', '뮤끄', '프렌냥'],
    team2A: ['해피토리', '뉴티365', '디다', '아비토랩'],
    team2B: ['씨퓨리', '리베니프', '리디에뜨', '에르보떼'],
    team3: ['하아르', '리서쳐스', '리프비기닝', '리서쳐스포우먼', '아르다오'],
    team4: ['베다이트', '데이배리어', '리프비기닝', '건강도감', '리서쳐스포우먼']
};

document.addEventListener('DOMContentLoaded', (event) => {
    const form = document.querySelector('form');
    const fileInput = document.querySelector('input[type="file"]');

    form.addEventListener('submit', (e) => {
        if (fileInput.files.length === 0) {
            e.preventDefault();
            alert('하나 이상의 파일을 업로드 해주세요!');
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');

    fileInput.addEventListener('change', function(e) {
        fileList.innerHTML = '';
        for (let i = 0; i < this.files.length; i++) {
            let file = this.files[i];
            let listItem = document.createElement('div');
            listItem.textContent = file.name;
            fileList.appendChild(listItem);
        }
    });

    const radios = document.querySelectorAll('input[type=radio][name="selected_team"]');
    const brandList = document.getElementById('brand-list');

    radios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const selectedTeam = e.target.value;
            const brands = teamBrands[selectedTeam];
            brandList.innerHTML = '<h3>브랜드 목록</h3><ul>' + 
                brands.map(brand => `<li>${brand}</li>`).join('') + 
                '</ul>';
        });
    });
});