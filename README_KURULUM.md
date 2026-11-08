# OTOMOTİV KAHOOT – CANLI BİLGİ YARIŞMASI

**Kaynak:** Kullanıcının yüklediği *H.K.S. CİLT-1111(1).pdf* – Hareket Kontrol Sistemleri Atölyesi; güç aktarma organları, kavrama sistemleri, tork konvertörleri ve mekanik vites kutuları. Her soruda kitap sayfası referansı yer alır. Sorular kitabın içeriğinden hareketle özgün hazırlanmıştır; kitaptaki sınav sorularının birebir kopyası değildir.

## Oyun neler yapar?
- Öğretmen bilgisayarından yeni bir yarışma odası açar. Oda kodu ve **o anki bağlantıyı içeren gerçek QR kodu** oluşturulur.
- Öğrenciler QR kodla telefondan bağlanıp isim yazar. Aynı anda en çok 80 öğrenci katılabilir (pratik sınır sunucu ve ağ kapasitesine bağlıdır).
- 32 soruluk havuzdan rastgele 15 soru seçilir. Her soruda **25 saniye** vardır.
- Her soruyu doğru ve hızlı yanıtlayan daha yüksek puan alır: 1000 temel + en çok 500 hız bonusu + en çok 400 seri bonusu. Yanlış yanıt sıfır puandır.
- Öğrencinin cevabı **sunucuda** doğrulanır ve bir soruya yalnızca bir kez cevap verilir.
- Öğretmen istediği an soru süresini sonlandırıp doğru yanıtı gösterebilir. Herkes cevap verirse doğru yanıt otomatik gösterilir. Süre dolunca da doğru yanıt otomatik açılır.
- Canlı liderlik tablosu, teknik SVG şemalar, soru sonu açıklama ve sonuç ekranı vardır.
- İnternet kullanmadan **aynı Wi-Fi ağı üzerindeki cihazlarla** da çalıştırılabilir (sunucu Python ile çalışan bir öğretmen bilgisayarıdır).

## 1) Windows bilgisayarda çalıştırma

1. ZIP arşivini açın. `Otomotiv_Kahoot_Canli` klasörüne girin.
2. Bilgisayarda **Python 3.10 veya üstü** yüklü olmalı. Kurarken `Add python.exe to PATH` seçeneğini işaretleyin.
3. `BASLAT_WINDOWS.bat` dosyasına çift tıklayın. İlk seferde QR üretim kütüphanesini internetten yükler; daha sonra sunucu başlar.
4. Öğretmen bilgisayarında `http://localhost:8000` adresini açın.
5. **Öğretmen • Oda oluştur** seçeneğini kullanın.
6. Öğrencilerin aynı Wi-Fi ağı üzerinden bağlanması için `ipconfig` komutuyla öğretmen bilgisayarının yerel IPv4 adresini öğrenin (örnek: `192.168.1.20`).
7. **Önemli:** Öğretmen kendi cihazında `localhost` ile oda açarsa oluşturulan QR öğrencilere uygun olmaz. Öğretmen de oyunu `http://192.168.1.20:8000` benzeri **yerel ağ IP adresi** üzerinden açmalı ve o adreste yeni oda oluşturmalıdır. Bu sayede QR kod öğrenci telefonlarında da erişilir.
8. Windows Güvenlik Duvarı erişim sorarsa özel ağ için Python'a izin verin. Öğretmen bilgisayarı ve telefonlar **aynı Wi-Fi** ağına bağlı olmalıdır. Misafir Wi-Fi ağında cihazlar birbirinden yalıtılmışsa bağlantı kurulmayabilir.

**Manuel başlatma (Windows/macOS/Linux):**

```bash
python -m pip install -r requirements.txt
python server.py
```

Terminal açık kaldığı sürece sunucu çalışır. Durdurmak için `Ctrl+C`.

## 2) İnternete yayınlama – Render + GitHub

Bu projede gerçek zamanlı sistem için Python tabanlı **tek sunucu** kullanılır. HTML dosyasını tek başına Drive'a, Netlify'a veya sıradan statik siteye koymak çok oyunculu eşitlemeyi çalıştırmaz.

1. `https://github.com` adresinde oturum açın, **New repository** ile örneğin `otomotiv-kahoot-canli` adlı bir depo oluşturun.
2. ZIP içindeki `Otomotiv_Kahoot_Canli` klasörünün **içeriğini** depoya yükleyin. Kök dizinde `server.py`, `requirements.txt`, `questions.json`, `render.yaml`, `public` bulunmalı.
3. `https://dashboard.render.com` adresinden **New > Web Service** seçin ve GitHub deponuzu bağlayın.
4. Ayarlar: **Language / Runtime = Python**, **Build Command = `pip install -r requirements.txt`**, **Start Command = `python server.py`**. Planı ve bölgeyi belirleyip dağıtımı başlatın. `render.yaml` dosyası da aynı parametreleri içerir; isterseniz Render Blueprint kurulumunu kullanabilirsiniz.
5. Dağıtım sonunda aldığınız `https://...onrender.com` adresini öğretmen bilgisayarında açın. **Öğretmen • Oda oluştur** seçeneğine tıklayın.
6. Akıllı tahtada QR kodu gösterin. Öğrenciler **herhangi bir yerden, internet üzerinden** telefonlarıyla katılabilir.
7. Öğretmen ekranı **gizli yetki anahtarı içeren URL** kullanır. Öğretmen bağlantısını öğrencilerle paylaşmayın. Öğrencilerle yalnızca QR kodu/katılım bağlantısını veya oda kodunu paylaşın.

**Render dokümanları:** https://render.com/docs/web-services ve https://render.com/docs/deploy-node-express-app (Node örneği; burada Python web servisi seçilecektir). Sunucu `PORT` ortam değişkenini ve `0.0.0.0` dinleme adresini destekler.

**Ücretsiz plan uyarısı:** Ücretsiz/uykuya alınabilen sunucularda uyku veya yeniden başlatma olduğunda aktif yarışma sıfırlanır. Sınıf içinde önemli bir oturum için uyumayan tek sunucu kullanın ve yarışma başlamadan bağlantıları kontrol edin. Uygulama verileri **bellekte tutulur**, veritabanına yazılmaz.

## 3) Sınıfta oynanış

1. Öğretmen `Öğretmen • Oda oluştur` ile oda açar, QR kodunu tahtada gösterir.
2. Öğrenciler karekodu okutur, isimlerini yazar.
3. Öğretmen `Yarışmayı başlat` der.
4. Her soru tahtada ve **öğrencinin telefonunda** görünür. Öğrenci tek bir yanıt verir.
5. Süre dolunca / herkes cevaplayınca doğru yanıt ve açıklaması görünür. Öğretmen `Sonraki soru`ya tıklar.
6. Son soru sonrası podyum görünür. İstenirse `Yeni yarışma başlat` kullanılabilir (aynı oyuncularla yeniden sıfırlanır).

## 4) İçerik ve özelleştirme

- `questions.json`: Sorular, 4 seçenek, doğru cevap indeksi `answer` (0=A, 1=B, 2=C, 3=D), açıklama, kaynak kitap sayfası ve görsel tipi. Değiştirdikten sonra sunucuyu yeniden başlatın.
- `server.py`: `QUESTION_SECONDS` (varsayılan 25), `QUESTION_COUNT` (varsayılan 15) ortam değişkenleriyle süre ve tur sayısı ayarlanabilir.
- `public/assets/app.js`: 5 SVG teknik çizim ve istemci işlevleri.
- `public/assets/style.css`: Tasarım ve telefon görünümü.
- Öğrenci adı dışında özel bilgi istenmez; isimler ve puanlar oturum sırasında bellektedir. Gerçek öğrenci adları yerine rumuz kullanılabilir.

## 5) Teknik ve güvenlik notları

- Bir oda yalnızca kendi gizli öğretmen anahtarıyla kontrol edilir. Öğrenci puanı yalnızca sunucuda hesaplanır. Yarışma başlamadan doğru cevaplar öğrenciye gönderilmez.
- Gerçek zamanlı güncellemeler **Server-Sent Events (SSE)** ile öğrencilere iletilir. Cevaplar POST istekleriyle sunucuya gönderilir.
- Sunucu belleği yeniden başlatılırsa oda, cevaplar ve puanlar silinir; yarışma kayıtları kalıcı değildir.
- Bu sürüm temel sınıf içi kullanım içindir; kurumsal kimlik doğrulama, kalıcı sonuç kaydı, çoklu sunucu eşitlemesi veya gelişmiş kötüye kullanım koruması bulunmaz.
- Görseller, çalışma materyalindeki kavramları desteklemek için hazırlanmış **özgün şematik SVG çizimleridir**; kitaptaki fotoğrafların birebir kopyası değildir.

## Sorun giderme

- **QR okutuluyor ama açılmıyor:** `localhost` yerine telefonun erişebildiği yerel IP veya HTTPS çevrim içi alan adından odayı yeniden oluşturun.
- **Telefonda hiç sayfa açılmıyor:** Aynı ağa bağlı mısınız? Misafir ağının cihaz izolasyonu açık mı? Güvenlik duvarı 8000 portuna izin veriyor mu?
- **Python bulunamadı:** Python kurulumu ve PATH ayarlarını kontrol edin; `py -3 server.py` komutunu deneyin.
- **QR görünmüyor:** `python -m pip install -r requirements.txt` komutunu çalıştırın.
- **Yarışma yarıda sıfırlandı:** Sunucu yeniden başlamış olabilir. Uyumayan bir sunucu kullanın.
