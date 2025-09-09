// 日付選択要素と地図コンテナを取得
const dateSelector = document.getElementById('date-selector');
const mapContainer = document.getElementById('map');

// 地図を初期化
const chibaCenter = [35.6076, 140.1063];
const map = L.map(mapContainer).setView(chibaCenter, 13);
const gsiTileLayer = L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png', {
    attribution: '国土地理院',
    maxZoom: 18,
    minZoom: 12
}).addTo(map);

// 全てのマーカーを保持するレイヤーグループ
const markers = L.layerGroup().addTo(map);

// --------------------------------------------------
// 営業日判定のためのヘルパー関数（PythonのロジックをJavaScriptで再現）
// --------------------------------------------------
function getWeekdayCode(date) {
    const day = date.getDate();
    const weekday = date.getDay(); // 0 (日) から 6 (土)
    const weekNum = Math.floor((day - 1) / 7) + 1;
    const weekday_index = (weekday === 0) ? 7 : weekday; // 日曜日を7に変換
    const code = (weekNum - 1) * 7 + weekday_index;
    return String(code).padStart(2, '0');
}

function openToday(codeStr, date) {
    if (!codeStr || codeStr === 'nan') {
        return false;
    }
    // 偶数月の判別
    if (codeStr.includes("EV") && (date.getMonth() + 1) % 2 === 1) {
        return false;
    }
    const todayCode = getWeekdayCode(date);
    const codes = codeStr.match(/.{1,2}/g);
    return codes && codes.includes(todayCode);
}

// --------------------------------------------------
// 地図のマーカーを更新するメイン関数
// --------------------------------------------------
function updateMarkers(selectedDate) {
    // 既存のマーカーをすべて削除
    markers.clearLayers();

    // JSONデータを読み込む
    fetch('kodomo_shokudo_data.json')
        .then(response => response.json())
        .then(data => {
            data.forEach(place => {
                if (place.lat && place.long) {
                    const isOpen = openToday(String(place.日時), selectedDate);

                    let iconUrl;
                    let iconSize;
                    if (isOpen) {
                        iconUrl = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png';
                        iconSize = [40, 65]; // 赤で大きめ
                    } else {
                        iconUrl = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png';
                        iconSize = [25, 41]; // 青で標準サイズ
                    }
                    
                    const customIcon = L.icon({
                        iconUrl: iconUrl,
                        iconSize: iconSize,
                        iconAnchor: [iconSize[0] / 2, iconSize[1]],
                        popupAnchor: [0, -iconSize[1]]
                    });

                    // ポップアップHTMLを作成
                    const popupHtml = `
                        <div style="white-space:nowrap;">
                            <b>${place["こども食堂の名称"] || ''}</b><br>
                            施設名：${place["施設名"] || ''}<br>
                            開催日：${place["開催日"] || ''}<br>
                            時間：${place["時間"] || ''}<br>
                            参加費用：${place["参加費用"] || ''}<br>
                            電話番号：${place["電話番号"] || ''}<br>
                            その他：${place["その他"] || ''}
                        </div>
                    `;

                    // マーカーを地図に追加
                    L.marker([place.lat, place.long], { icon: customIcon })
                        .bindPopup(popupHtml)
                        .addTo(markers);
                }
            });
        })
        .catch(error => console.error('Error loading the data:', error));
}

// --------------------------------------------------
// イベントリスナーと初期表示
// --------------------------------------------------
// 日付選択フォームの値が変更されたらマーカーを更新
dateSelector.addEventListener('change', (event) => {
    const selectedDate = new Date(event.target.value);
    if (!isNaN(selectedDate.getTime())) {
        updateMarkers(selectedDate);
    }
});

// ページ読み込み時に今日の日付を初期値として設定
const today = new Date();
const todayString = today.toISOString().split('T')[0];
dateSelector.value = todayString;

// 初回表示
updateMarkers(today);