from django.shortcuts import render
from django.http import Http404
from .data import SEHIRLER
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import KayitFormu
from django.shortcuts import redirect
from .models import Yorum, Favori, Puanlama, KullaniciRotasi, RotaDuragi, IletisimMesaji, GeziPaylasimi, GeziPaylasimBegeni, GeziPaylasimYorum,Profil
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from django.core.mail import send_mail
from django.conf import settings


def home(request):
    populer_sehirler = [
        "antalya",
        "istanbul",
        "izmir",
        "mugla",
        "aydin",
        "balikesir",
        "canakkale",
        "nevsehir",
        "trabzon",
        "rize",
        "mardin",
        "sanliurfa",
    ]
    return render(request, "travel/home.html", {
        "populer_sehirler": [
            SEHIRLER[slug] | {"slug": slug}
            for slug in populer_sehirler
        ]
    })


def sehirler(request):
    arama = request.GET.get("q", "")

    plaka_sirasi = [
        "adana", "adiyaman", "afyonkarahisar", "agri", "amasya", "ankara",
        "antalya", "artvin", "aydin", "balikesir", "bilecik", "bingol",
        "bitlis", "bolu", "burdur", "bursa", "canakkale", "cankiri",
        "corum", "denizli", "diyarbakir", "edirne", "elazig", "erzincan",
        "erzurum", "eskisehir", "gaziantep", "giresun", "gumushane",
        "hakkari", "hatay", "isparta", "mersin", "istanbul", "izmir",
        "kars", "kastamonu", "kayseri", "kirklareli", "kirsehir", "kocaeli",
        "konya", "kutahya", "malatya", "manisa", "kahramanmaras", "mardin",
        "mugla", "mus", "nevsehir", "nigde", "ordu", "rize", "sakarya",
        "samsun", "siirt", "sinop", "sivas", "tekirdag", "tokat", "trabzon",
        "tunceli", "sanliurfa", "usak", "van", "yozgat", "zonguldak",
        "aksaray", "bayburt", "karaman", "kirikkale", "batman", "sirnak",
        "bartin", "ardahan", "igdir", "yalova", "karabuk", "kilis",
        "osmaniye", "duzce"
    ]

    plaka_index = {slug: index for index, slug in enumerate(plaka_sirasi)}

    tum_sehirler = []

    for slug, sehir in SEHIRLER.items():
        if arama.lower() in sehir["isim"].lower():
            yeni_sehir = sehir.copy()
            yeni_sehir["slug"] = slug
            tum_sehirler.append(yeni_sehir)

    tum_sehirler.sort(key=lambda sehir: plaka_index.get(sehir["slug"], 999))

    return render(request, "travel/sehirler.html", {
        "sehirler": tum_sehirler,
        "arama": arama
    })


def sehir_detay(request, slug):
    sehir = SEHIRLER.get(slug)

    if sehir is None:
        raise Http404("Şehir bulunamadı")

    return render(request, "travel/sehir_detay.html", {
        "sehir": sehir,
        "slug": slug
    })


def ilce_detay(request, sehir_slug, ilce_slug):
    sehir = SEHIRLER.get(sehir_slug)

    if sehir is None:
        raise Http404("Şehir bulunamadı")

    secilen_ilce = None

    for ilce in sehir.get("ilceler", []):
        if ilce.get("slug") == ilce_slug:
            secilen_ilce = ilce
            break

    if secilen_ilce is None:
        raise Http404("İlçe bulunamadı")

    if request.method == "POST" and request.user.is_authenticated:
        baslik = request.POST.get("baslik", "")
        yorum_metni = request.POST.get("yorum", "")

        if yorum_metni:
            Yorum.objects.create(
                kullanici=request.user,
                sehir_slug=sehir_slug,
                ilce_slug=ilce_slug,
                baslik=baslik,
                yorum=yorum_metni
            )

        return redirect("ilce_detay", sehir_slug=sehir_slug, ilce_slug=ilce_slug)

    yorumlar = Yorum.objects.filter(
        sehir_slug=sehir_slug,
        ilce_slug=ilce_slug
    ).order_by("-olusturma_tarihi")

    ortalama_puan = Puanlama.objects.filter(
        sehir_slug=sehir_slug,
        ilce_slug=ilce_slug
    ).aggregate(Avg("puan"))["puan__avg"]

    kullanici_puani = None

    if request.user.is_authenticated:
        kullanici_puani = Puanlama.objects.filter(
            kullanici=request.user,
            sehir_slug=sehir_slug,
            ilce_slug=ilce_slug
        ).first()

    favoride_mi = False

    if request.user.is_authenticated:
        favoride_mi = Favori.objects.filter(
            kullanici=request.user,
            sehir_slug=sehir_slug,
            ilce_slug=ilce_slug
        ).exists()

    return render(request, "travel/ilce_detay.html", {
        "sehir": sehir,
        "sehir_slug": sehir_slug,
        "ilce": secilen_ilce,
        "yorumlar": yorumlar,
        "favoride_mi": favoride_mi,
        "ortalama_puan": ortalama_puan,
        "kullanici_puani": kullanici_puani
    })


def arama(request):
    q = request.GET.get("q", "").strip()
    sonuclar = []

    if q:
        q_lower = q.lower()

        for sehir_slug, sehir in SEHIRLER.items():

            if q_lower in sehir.get("isim", "").lower():
                sonuclar.append({
                    "baslik": sehir.get("isim"),
                    "tur": "Şehir",
                    "aciklama": sehir.get("aciklama", ""),
                    "url": f"/sehir/{sehir_slug}/",
                    "resim": f"travel/images/sehir-fotograflari/{sehir.get('resim')}"
                })

            for ilce in sehir.get("ilceler", []):
                ilce_slug = ilce.get("slug")

                if q_lower in ilce.get("isim", "").lower():
                    sonuclar.append({
                        "baslik": ilce.get("isim"),
                        "tur": "İlçe",
                        "aciklama": ilce.get("aciklama", ""),
                        "url": f"/sehir/{sehir_slug}/ilce/{ilce_slug}/",
                        "resim": f"travel/images/ilce-fotograflari/{ilce.get('resim')}"
                    })

                aranacak_alanlar = [
                    ("gezilecek_yerler", "Gezilecek Yer"),
                    ("plajlar", "Plaj"),
                    ("tarihi_yerler", "Tarihi Yer"),
                    ("muzeler", "Müze"),
                    ("dogal_guzellikler", "Doğal Güzellik"),
                    ("aktiviteler", "Aktivite"),
                    ("ekstrem_sporlar", "Ekstrem Spor"),
                    ("yemek_nerede", "Yeme İçme"),
                ]

                for alan, tur in aranacak_alanlar:
                    for item in ilce.get(alan, []):
                        baslik = item.get("baslik", "")
                        aciklama = item.get("aciklama", "")

                        if q_lower in baslik.lower() or q_lower in aciklama.lower():
                            sonuclar.append({
                                "baslik": baslik,
                                "tur": tur,
                                "aciklama": aciklama,
                                "url": f"/sehir/{sehir_slug}/ilce/{ilce_slug}/",
                                "resim": f"travel/images/ilce-fotograflari/{item.get('resim')}"
                            })

    return render(request, "travel/arama.html", {
        "q": q,
        "sonuclar": sonuclar
    })


def kayit_ol(request):
    if request.method == "POST":
        form = KayitFormu(request.POST)

        if form.is_valid():
            kullanici = form.save(commit=False)
            kullanici.email = form.cleaned_data["email"]
            kullanici.save()

            login(request, kullanici)
            return redirect("home")
    else:
        form = KayitFormu()

    return render(request, "travel/kayit_ol.html", {
        "form": form
    })


def giris_yap(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            kullanici = form.get_user()
            login(request, kullanici)
            return redirect("home")
    else:
        form = AuthenticationForm()

    return render(request, "travel/giris_yap.html", {
        "form": form
    })


def cikis_yap(request):
    logout(request)
    return redirect("home")


@login_required
def favori_ekle(request, sehir_slug, ilce_slug):
    sehir = SEHIRLER.get(sehir_slug)

    if sehir is None:
        raise Http404("Şehir bulunamadı")

    secilen_ilce = None

    for ilce in sehir.get("ilceler", []):
        if ilce.get("slug") == ilce_slug:
            secilen_ilce = ilce
            break

    if secilen_ilce is None:
        raise Http404("İlçe bulunamadı")

    favori, olusturuldu = Favori.objects.get_or_create(
        kullanici=request.user,
        sehir_slug=sehir_slug,
        ilce_slug=ilce_slug,
        yer_baslik=secilen_ilce.get("isim"),
        yer_turu="İlçe"
    )

    if olusturuldu:
        messages.success(request, f"{secilen_ilce.get('isim')} favorilerine eklendi.")
    else:
        messages.info(request, f"{secilen_ilce.get('isim')} zaten favorilerinde.")

    return redirect("ilce_detay", sehir_slug=sehir_slug, ilce_slug=ilce_slug)


@login_required
def favorilerim(request):
    favoriler = Favori.objects.filter(
        kullanici=request.user
    ).order_by("-eklenme_tarihi")

    return render(request, "travel/favorilerim.html", {
        "favoriler": favoriler
    })


@login_required
def favori_cikar(request, sehir_slug, ilce_slug):
    Favori.objects.filter(
        kullanici=request.user,
        sehir_slug=sehir_slug,
        ilce_slug=ilce_slug
    ).delete()

    messages.success(request, "Favorilerden çıkarıldı.")

    return redirect("ilce_detay", sehir_slug=sehir_slug, ilce_slug=ilce_slug)

@login_required
def puan_ver(request, sehir_slug, ilce_slug):
    if request.method == "POST":
        puan = int(request.POST.get("puan", 0))

        if 1 <= puan <= 5:
            Puanlama.objects.update_or_create(
                kullanici=request.user,
                sehir_slug=sehir_slug,
                ilce_slug=ilce_slug,
                defaults={"puan": puan}
            )

            messages.success(request, "Puanın kaydedildi.")

    return redirect("ilce_detay", sehir_slug=sehir_slug, ilce_slug=ilce_slug)


@login_required
def favorilerimden_cikar(request, favori_id):
    favori = Favori.objects.filter(
        id=favori_id,
        kullanici=request.user
    ).first()

    if favori:
        favori.delete()
        messages.success(request, "Favori listenizden kaldırıldı.")

    return redirect("favorilerim")


@login_required
def rotalarim(request):
    rotalar = KullaniciRotasi.objects.filter(
        kullanici=request.user
    ).order_by("-olusturma_tarihi")

    return render(request, "travel/rotalarim.html", {
        "rotalar": rotalar
    })


@login_required
def rota_olustur(request):
    if request.method == "POST":
        baslik = request.POST.get("baslik", "")
        aciklama = request.POST.get("aciklama", "")
        sehir_slug = request.POST.get("sehir_slug", "")

        if baslik and sehir_slug:
            KullaniciRotasi.objects.create(
                kullanici=request.user,
                baslik=baslik,
                aciklama=aciklama,
                sehir_slug=sehir_slug
            )

            messages.success(request, "Rotan oluşturuldu.")
            return redirect("rotalarim")

    return render(request, "travel/rota_olustur.html", {
        "sehirler": SEHIRLER
    })


def hakkimizda(request):
    return render(request, "travel/hakkimizda.html")


def iletisim(request):
    if request.method == "POST":
        ad = request.POST.get("ad", "")
        email = request.POST.get("email", "")
        konu = request.POST.get("konu", "")
        mesaj = request.POST.get("mesaj", "")

        if ad and email and konu and mesaj:
            IletisimMesaji.objects.create(
                ad=ad,
                email=email,
                konu=konu,
                mesaj=mesaj
            )

            send_mail(
                subject=f"Rota Türkiye İletişim: {konu}",
                message=f"Ad: {ad}\nE-mail: {email}\n\nMesaj:\n{mesaj}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=["rotaturkiye0@gmail.com"],
                fail_silently=False,
            )

            messages.success(request, "Mesajınız başarıyla gönderildi.")
            return redirect("iletisim")

    return render(request, "travel/iletisim.html")



@login_required
def rota_detay(request, rota_id):
    rota = KullaniciRotasi.objects.filter(
        id=rota_id,
        kullanici=request.user
    ).first()

    if rota is None:
        raise Http404("Rota bulunamadı")

    if request.method == "POST":
        favori_id = request.POST.get("favori_id", "")
        yer_adi = request.POST.get("yer_adi", "")
        notlar = request.POST.get("notlar", "")
        sira = request.POST.get("sira", 1)

        if favori_id:
            favori = Favori.objects.filter(
                id=favori_id,
                kullanici=request.user
            ).first()

            if favori:
                yer_adi = favori.yer_baslik
                notlar = f"{favori.yer_turu} olarak favorilerden eklendi."

        if yer_adi:
            RotaDuragi.objects.create(
                rota=rota,
                yer_adi=yer_adi,
                notlar=notlar,
                sira=sira
            )

            messages.success(request, "Durak rotaya eklendi.")
            return redirect("rota_detay", rota_id=rota.id)

    favoriler = Favori.objects.filter(
        kullanici=request.user
    ).order_by("-eklenme_tarihi")

    return render(request, "travel/rota_detay.html", {
        "rota": rota,
        "duraklar": rota.duraklar.all(),
        "favoriler": favoriler
    })


@login_required
def durak_sil(request, durak_id):
    durak = RotaDuragi.objects.filter(
        id=durak_id,
        rota__kullanici=request.user
    ).first()

    if durak is None:
        raise Http404("Durak bulunamadı")

    rota_id = durak.rota.id
    durak.delete()

    messages.success(request, "Durak kaldırıldı.")

    return redirect("rota_detay", rota_id=rota_id)


@login_required
def rota_sil(request, rota_id):
    rota = KullaniciRotasi.objects.filter(
        id=rota_id,
        kullanici=request.user
    ).first()

    if rota is None:
        raise Http404("Rota bulunamadı")

    rota.delete()

    messages.success(request, "Rota silindi.")

    return redirect("rotalarim")



@login_required
def rota_duzenle(request, rota_id):
    rota = KullaniciRotasi.objects.filter(
        id=rota_id,
        kullanici=request.user
    ).first()

    if rota is None:
        raise Http404("Rota bulunamadı")

    if request.method == "POST":
        rota.baslik = request.POST.get("baslik", "")
        rota.aciklama = request.POST.get("aciklama", "")
        rota.sehir_slug = request.POST.get("sehir_slug", "")
        rota.save()

        messages.success(request, "Rota güncellendi.")
        return redirect("rotalarim")

    return render(request, "travel/rota_duzenle.html", {
        "rota": rota,
        "sehirler": SEHIRLER
    })


@login_required
def durak_duzenle(request, durak_id):
    durak = RotaDuragi.objects.filter(
        id=durak_id,
        rota__kullanici=request.user
    ).first()

    if durak is None:
        raise Http404("Durak bulunamadı")

    if request.method == "POST":
        durak.sira = request.POST.get("sira", 1)
        durak.yer_adi = request.POST.get("yer_adi", "")
        durak.notlar = request.POST.get("notlar", "")
        durak.save()

        messages.success(request, "Durak güncellendi.")
        return redirect("rota_detay", rota_id=durak.rota.id)

    return render(request, "travel/durak_duzenle.html", {
        "durak": durak
    })


def paylasilan_rota(request, paylasim_kodu):
    rota = KullaniciRotasi.objects.filter(
        paylasim_kodu=paylasim_kodu
    ).first()

    if rota is None:
        raise Http404("Rota bulunamadı")

    return render(request, "travel/paylasilan_rota.html", {
        "rota": rota,
        "duraklar": rota.duraklar.all()
    })


def gezi_paylasimlari(request):
    secilen_sehir = request.GET.get("sehir", "")

    paylasimlar = GeziPaylasimi.objects.all().order_by("-olusturma_tarihi")

    if secilen_sehir:
        paylasimlar = paylasimlar.filter(sehir_slug=secilen_sehir)

    begenilen_paylasimlar = []

    if request.user.is_authenticated:
        begenilen_paylasimlar = GeziPaylasimBegeni.objects.filter(
            kullanici=request.user
        ).values_list("paylasim_id", flat=True)

    return render(request, "travel/gezi_paylasimlari.html", {
        "paylasimlar": paylasimlar,
        "begenilen_paylasimlar": begenilen_paylasimlar,
        "sehirler": SEHIRLER,
        "secilen_sehir": secilen_sehir
    })


@login_required
def gezi_paylas(request):
    if request.method == "POST":
        baslik = request.POST.get("baslik", "")
        sehir_slug = request.POST.get("sehir_slug", "")
        aciklama = request.POST.get("aciklama", "")
        fotograf = request.FILES.get("fotograf")

        if baslik and sehir_slug and aciklama and fotograf:
            GeziPaylasimi.objects.create(
                kullanici=request.user,
                baslik=baslik,
                sehir_slug=sehir_slug,
                aciklama=aciklama,
                fotograf=fotograf
            )

            messages.success(request, "Paylaşımın yayınlandı.")
            return redirect("gezi_paylasimlari")

    return render(request, "travel/gezi_paylas.html", {
        "sehirler": SEHIRLER
    })


@login_required
def gezi_paylasim_begen(request, paylasim_id):
    paylasim = GeziPaylasimi.objects.filter(id=paylasim_id).first()

    if paylasim is None:
        raise Http404("Paylaşım bulunamadı")

    begeni = GeziPaylasimBegeni.objects.filter(
        kullanici=request.user,
        paylasim=paylasim
    ).first()

    if begeni:
        begeni.delete()
        messages.info(request, "Beğeni kaldırıldı.")
    else:
        GeziPaylasimBegeni.objects.create(
            kullanici=request.user,
            paylasim=paylasim
        )
        messages.success(request, "Paylaşımı beğendin.")

    return redirect("gezi_paylasimlari")


@login_required
def gezi_paylasim_sil(request, paylasim_id):
    paylasim = GeziPaylasimi.objects.filter(
        id=paylasim_id,
        kullanici=request.user
    ).first()

    if paylasim is None:
        raise Http404("Paylaşım bulunamadı")

    paylasim.delete()

    messages.success(request, "Paylaşım kaldırıldı.")

    return redirect("gezi_paylasimlari")


@login_required
def gezi_paylasim_yorum_ekle(request, paylasim_id):
    paylasim = GeziPaylasimi.objects.filter(id=paylasim_id).first()

    if paylasim is None:
        raise Http404("Paylaşım bulunamadı")

    if request.method == "POST":
        yorum = request.POST.get("yorum", "")

        if yorum:
            GeziPaylasimYorum.objects.create(
                kullanici=request.user,
                paylasim=paylasim,
                yorum=yorum
            )

            messages.success(request, "Yorumun eklendi.")

    return redirect("gezi_paylasim_detay", paylasim_id=paylasim.id)


@login_required
def gezi_paylasim_yorum_sil(request, yorum_id):
    yorum = GeziPaylasimYorum.objects.filter(id=yorum_id).first()

    if yorum is None:
        raise Http404("Yorum bulunamadı")

    paylasim_id = yorum.paylasim.id

    if yorum.kullanici == request.user or yorum.paylasim.kullanici == request.user:
        yorum.delete()
        messages.success(request, "Yorum silindi.")
    else:
        raise Http404("Bu yorumu silme yetkin yok")

    return redirect("gezi_paylasim_detay", paylasim_id=paylasim_id)



def gezi_paylasim_detay(request, paylasim_id):
    paylasim = GeziPaylasimi.objects.filter(id=paylasim_id).first()

    if paylasim is None:
        raise Http404("Paylaşım bulunamadı")

    begenildi_mi = False

    if request.user.is_authenticated:
        begenildi_mi = GeziPaylasimBegeni.objects.filter(
            kullanici=request.user,
            paylasim=paylasim
        ).exists()

    yorumlar = GeziPaylasimYorum.objects.filter(
        paylasim=paylasim
    ).order_by("-olusturma_tarihi")

    return render(request, "travel/gezi_paylasim_detay.html", {
        "paylasim": paylasim,
        "begenildi_mi": begenildi_mi,
        "yorumlar": yorumlar
    })


@login_required
def paylasimlarim(request):
    paylasimlar = GeziPaylasimi.objects.filter(
        kullanici=request.user
    ).order_by("-olusturma_tarihi")

    return render(request, "travel/paylasimlarim.html", {
        "paylasimlar": paylasimlar
    })


@login_required
def profilim(request):
    profil, olusturuldu = Profil.objects.get_or_create(
    kullanici=request.user)
    paylasim_sayisi = GeziPaylasimi.objects.filter(
        kullanici=request.user
    ).count()

    rota_sayisi = KullaniciRotasi.objects.filter(
        kullanici=request.user
    ).count()

    favori_sayisi = Favori.objects.filter(
        kullanici=request.user
    ).count()

    son_paylasimlar = GeziPaylasimi.objects.filter(
        kullanici=request.user
    ).order_by("-olusturma_tarihi")[:3]

    return render(request, "travel/profilim.html", {
        "paylasim_sayisi": paylasim_sayisi,
        "rota_sayisi": rota_sayisi,
        "favori_sayisi": favori_sayisi,
        "son_paylasimlar": son_paylasimlar,
        "profil": profil,
    })


@login_required
def profil_duzenle(request):
    profil, olusturuldu = Profil.objects.get_or_create(
        kullanici=request.user
    )

    if request.method == "POST":
        fotograf = request.FILES.get("fotograf")

        if fotograf:
            profil.fotograf = fotograf
            profil.save()
            messages.success(request, "Profil fotoğrafın güncellendi.")
            return redirect("profilim")

    return render(request, "travel/profil_duzenle.html", {
        "profil": profil
    })


def gizlilik_politikasi(request):
    return render(request, "travel/gizlilik_politikasi.html")

def kullanim_sartlari(request):
    return render(request, "travel/kullanim_sartlari.html")

def cerez_politikasi(request):
    return render(request, "travel/cerez_politikasi.html")