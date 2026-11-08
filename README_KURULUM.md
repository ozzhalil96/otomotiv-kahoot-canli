# Otomotiv Kahoot — Canlı Yarışma 4.0

**Kaynak:** Öğretmen tarafından sağlanan *H.K.S. CİLT-1111(1).pdf* (Hareket Kontrol Sistemleri Atölyesi). Güç aktarma organları, kavrama, tork konvertörü ve mekanik vites kutuları üzerine özgün sorular hazırlanmıştır. Kitabın basılı sayfa numaraları sorularda belirtilir.

## Bu sürümde neler var?

- **30 soru:** 10 kolay (15 saniye), 10 orta (25 saniye), 10 zor (40 saniye). Gruplar sırayla, sorular grup içinde karışık gelir.
- **QR ile bireysel katılım:** Herkes kendi telefonundan katılır. Öğretmen soruları ve geçişleri yönetir. Gerçek zamanlı bağlantı Server-Sent Events ile sağlanır.
- **Canlı sıralama animasyonları:** Sıralamada yükseliş animasyonu ve her 5 soruda ara liderlik duyurusu.
- **Sürpriz arıza soruları:** Müşteri şikâyeti ve teknik bulguların değerlendirilmesi.
- **Görselden parça bulma:** İşaretli parçayı veya elemanı gösteren özgün teknik SVG şemaları.
- **Öğretmen analiz paneli:** Finalde konu bazlı başarı çubukları, soru bazlı doğru/yanlış/boş adetleri, CSV indirme.
- **Puan sistemi:** Doğru cevap 1000 temel + en fazla 500 hız bonusu + en fazla 400 seri bonusu. Yanlış cevap 0 puan.
- **Sesler:** Yalnızca öğretmen ekranında özgün Web Audio arka plan melodisi, açılış, doğru/yanlış ve son 5 saniye efektleri. Ses aç/kapat ve seviye kontrolü.
- **İmza:** Sağ altta “Otomotiv Teknolojisi Öğretmeni Halil ÖZ” ve “Bursa Şehit Ömer Halisdemir MTAL”.

## GitHub klasör düzeni — ÖNEMLİ

ZIP'in **içeriğini** GitHub deponuzun ana dizinine yükleyin, ZIP dosyasının kendisini veya içinde fazladan bir üst klasörü yüklemeyin.

```text
otomotiv-kahoot-canli/
  server.py
  questions.json
  requirements.txt
  render.yaml
  README_KURULUM.md
  BASLAT_WINDOWS.bat
  public/
    index.html
    assets/
      app.js
      sound.js
      style.css
```

Özellikle `index.html` **public klasöründe**; `app.js`, `style.css`, `sound.js` ise **public/assets klasöründe** olmalıdır. Ana dizindeki aynı adlı dosyalar uygulama tarafından **kullanılmaz**. Önceki GitHub yüklemenizde bu fazlalıklar varsa karışıklığı önlemek için silmek faydalıdır; esas olan doğru klasördeki dosyaların güncellenmesidir.

### GitHub Web arayüzüyle güncelleme

1. Depodaki `public/index.html` dosyasını en son sürümle değiştirin.
2. `public/assets/app.js`, `public/assets/style.css`, `public/assets/sound.js` dosyalarını güncelleyin.
3. Depo **kökündeki** `server.py` ve `questions.json` dosyalarını güncelleyin.
4. Her değişiklik için **Commit changes** deyin.
5. Render → Web Service → **Manual Deploy → Deploy latest commit**.
6. Tarayıcıda sayfayı `Ctrl+F5` ile yenileyin. Üst kısımda **SÜRÜM 4.0 · ANALİZ + GÖRSEL + MÜZİK** görünmelidir.

**Uyarı:** ZIP'i GitHub sitesine tek dosya olarak yüklemek uygulamayı güncellemez. Render'ın GitHub ana dalınıza (`main`) bağlı olduğunu kontrol edin.

## Render üzerinde Python yüklemeden çalıştırma

Bu adımlar **kendi bilgisayarınıza Python kurmayı gerektirmez**:

1. GitHub üzerinde bir repository oluşturup yukarıdaki klasör yapısıyla dosyaları yükleyin.
2. https://dashboard.render.com → **New → Web Service** → GitHub deposunu bağlayın.
3. Runtime: **Python**; Build Command: `pip install -r requirements.txt`; Start Command: `python server.py`; Root Directory: boş; plan: kullanımınıza uygun plan.
4. Yayımlandığında `https://<sunucu>.onrender.com` bağlantısını açın; öğretmen odası oluşturun.
5. Öğrenciler QR kodu okutarak **farklı Wi-Fi veya mobil bağlantılardan** katılabilir. Öğretmenin gizli `/host?token=...` adresini öğrencilere göndermeyin.
6. Yeni yarışma başlamadan önce 2 farklı cihazla katılım ve puan güncellemesini deneyin.

**Render ücretsiz planı:** Sunucu uykuya geçebilir. Oyun odaları ve sonuçlar bellektedir; yeniden başlatma sonrası kaybolur. Sınıf sınavı veya yüksek katılımlı yarışma için güvenilir/uyumayan bir sunucu kullanın.

## İsteğe bağlı yerel kullanım

Python kurulu olan bir bilgisayarda:

```bash
pip install -r requirements.txt
python server.py
```

`http://localhost:8000` yalnızca o bilgisayardan açılır. Aynı Wi-Fi'deki öğrencilerin bağlanması için öğretmen oyunu bilgisayarın erişilebilir LAN IP adresinden açmalı ve QR kodu o adresten üretmelidir. **Windows bilgisayarınıza Python kuramıyorsanız Render yöntemini kullanın.**

## Öğretmen analiz raporu

30. sorunun sonunda yalnızca öğretmen ekranında **Öğretmen analiz paneli** görünür:

- Her konu için başarı yüzdesi
- Soru başına doğru, yanlış ve cevap vermeyen sayıları
- Başarı oranı %50'nin altındaki soruların vurgulanması
- **Analizi CSV olarak indir**: Microsoft Excel'de açılabilen, noktalı virgülle ayrılmış ve Türkçe karakterleri destekleyen dosya. Ek olarak A/B/C/D cevap sayıları ve ortalama yanıtlama süreleri bulunur.

CSV yalnızca öğretmenin oturum anahtarıyla alınabilir. Oturum verileri kalıcı olarak saklanmaz; raporu oyun bitince indirin.

## Sorular ve teknik notlar

- `questions.json` 30 soru içerir: `difficulty`, `topic`, `q`, `options`, `answer` (0=A, 1=B, 2=C, 3=D), `page`, `explanation`, `visual` ve bazı sorularda `kind` alanları vardır.
- Görseller kitap fotoğraflarının kopyası değil, özgün şematik çizimlerdir.
- Sunucu puanı hesaplar ve öğrencilere cevap açıklanana dek doğru seçeneği göndermez.
- Sınıf içi ölçme değerlendirmede teknik uygunluğu öğretmenin kontrol etmesi önerilir.
- Tarayıcılar, kullanıcı etkileşimi gerçekleşmeden ses oynatmayı kısıtlayabilir. Öğretmen odasını açıp **Sesi aç / Intro** kontrolüyle sesi etkinleştirebilir.
- Python web sunucusu yalnızca tek işlem/bellek üzerinde oda bilgisi tutar; birden fazla kopya arasında canlı oturum eşitlemesi yoktur.

## SÜRÜM 5.0: Kişisel tekrar ve soru editörü

- **Öğrenciler:** Yarışma bittikten sonra sonuç ekranında yalnızca kendi yanlış/boş bıraktıkları soruları, verdikleri yanıtları, doğru şıkkı ve teknik açıklamayı görür. Başka öğrencilerin cevapları gösterilmez.
- **Öğretmen:** Odayı oluşturduktan sonra bekleme ekranının alt kısmında **Soruları yönet** panelini açabilir. Soru ekleyebilir, değiştirebilir, silebilir, dört şıkkı, doğru şıkkı, zorluğu, soru türünü, görseli, konuyu ve kitap sayfasını değiştirebilir. Öğretmen anahtarı olmadan bu işlemler yapılamaz.
- **Güvenlik:** Soru bankası ve doğru yanıtlar öğrenciye yarışma sırasında gönderilmez. Sorular yarışma oynanırken düzenlenemez.
- **30 soruluk format:** Sistem 10 kolay + 10 orta + 10 zor soruyu seçer. Her düzeyde en az 10 soru bulundurun. Bu düzeylerin herhangi birinde daha az soru bırakılırsa yarışma 30'dan kısa olacaktır.

### ÖNEMLİ: Render'da kalıcı kaydetme

Render'ın Free servisi üzerinde diske yazılan dosyalar **yeniden başlatma/yeniden dağıtım sonrasında kalıcı değildir**. GitHub ayarları olmadan panelde yaptığınız düzenlemeler çalışan sunucuda geçerli olur, fakat daha sonra kaybolabilir. Her düzenlemeden sonra **JSON yedeğini indir** seçeneğini kullanın.

Soru panelinden yaptığınız değişikliklerin **doğrudan GitHub'daki `questions.json` dosyasına kalıcı işlenmesi** için:

1. GitHub'da Fine-grained personal access token oluşturun. Yalnızca oyun deposuna erişim ve **Contents: Read and write** yetkisi verin. Token'ı öğrencilere ya da depodaki dosyalara KESİNLİKLE koymayın.
2. Render -> `otomotiv-kahoot-canli` servisi -> **Environment** alanına iki gizli değişken ekleyin:
   - `GITHUB_REPO`: `kullanici-adi/otomotiv-kahoot-canli` (gerçek GitHub kullanıcı ve depo adını yazın).
   - `GITHUB_WRITE_TOKEN`: GitHub'dan oluşturduğunuz token.
3. Render'da **Auto-Deploy** ayarını kapatın. Yoksa panelde soru değiştirince GitHub'a commit atılır ve hemen yeni dağıtım tetiklenerek aktif oda sıfırlanabilir.
4. Bu ayarlardan sonra oluşturulan öğretmen odasında soru kaydettiğinizde sunucu `questions.json` dosyasını GitHub'a commit eder. Soru bankası GitHub'da kalıcıdır. **Değişiklikleri mümkünse sınıf başlamadan yapın.** Render'da manuel yeniden dağıtım yapınca yeni dosya yüklenir.

GitHub token ayarı olmadan da öğretmen editörü çalışır. Önemli: öğretmen bağlantısındaki gizli oturum anahtarını başkalarıyla paylaşmayın; yalnızca katılım QR kodunu gösterin.

### GitHub yükleme

ZIP açıldığında **ana dizinde** `server.py`, `questions.json`, `requirements.txt`, `render.yaml`, `README_KURULUM.md` ve `public/` klasörü bulunur. `public/` içinde `index.html`; `public/assets/` içinde `app.js`, `sound.js`, `style.css` vardır. GitHub'da bu konumlara yükleyin. ZIP'i doğrudan GitHub'a yüklemeyin.
