# UwUchan

Implementasi protokol WhatsApp Web pakai Nusantara (`.ns`).

## Pasang

```bash
nusa get github.com/NusaLang/UwUchan
```

```
projectmu/
├── main.ns
└── nusantara_modules/
    └── UwUchan/
```

Butuh plugin `crypto`, `sqlite`, sama `ws` dari Nusantara.

## Pakai

```
buat HM = impor("UwUchan");
buat KL = HM.KL; buat MS = HM.MS; buat MEDIA = HM.MEDIA; buat SEC = HM.SEC;
buat AS = HM.AS; buat PRES = HM.PRES; buat USER = HM.USER; buat NEWS = HM.NEWS;
buat CALL = HM.CALL; buat BC = HM.BC; buat PB = HM.PB; buat JID = HM.JID; buat ST = HM.ST;

KL.KirimBootstrap(k);
```

Loop koneksi:

```
KL.KirimBootstrap(k);
KL.TikKeepalive(k);      // panggil tiap iterasi loop terima
KL.ProsesNode(k, node);  // dispatcher tiap node masuk
```

`k` minimal isinya:

```
buat k = peta_baru();
k["ws_id"] = ws_resp["id"];
k["noise_socket"] = HS.LakukanHandshake(io, noise_kp, identity_kp, jid, reg_id, "Nama Bot Kamu");
k["parser"] = FS.ParserBaru();
k["session_data"] = ST.MuatSesi("main");
k["identity_kp"] = identity_kp;
k["noise_kp"] = noise_kp;
k["our_registration_id"] = reg_id;
k["our_signed_prekey_priv"] = signed_prekey_priv;
k["retry_ctx"] = MS.SiapkanKonteksRetry(identity_kp, session_data);
k["waBot"] = waBot;                  // butuh HandleMessage(sender, teks, from_me)
k["DB"] = DB;                        // butuh SimpanLIDJID(lid, jid)
k["pesan_grup_terkirim"] = peta_baru();
k["epoch"] = epoch_state;
k["epoch_saya"] = epoch_state["now"];
```

Contoh lengkap ada di `main.ns` repo ndlabs-bot.

Nama device yang muncul di "Linked Devices" HP diatur lewat parameter
terakhir `LakukanHandshake` — `kosong` buat default `"UwUchan"`. Cuma
berlaku pas pairing baru (registrasi), gak ngaruh ke device yang udah
ke-pairing.

### `WaApi`

```
buat wa = KL.buat_api(k, konteks);

wa.KirimTeks("halo dari UwUchan");
wa.KirimKutip("balesan");
wa.KirimGambar("/tmp/foto.jpg", "caption");
wa.KirimGambarKutip("/tmp/foto.jpg", "caption");
wa.KirimVideo("/tmp/klip.mp4", "caption");
wa.KirimDokumen("/tmp/lap.pdf", "laporan.pdf", "application/pdf");
wa.KirimAudio("/tmp/vn.ogg", "audio/ogg", benar);
wa.KirimStiker("/tmp/stiker.webp", salah, kosong);
wa.KirimLokasi("ND-Labs", "Jakarta", kosong);
wa.KirimPoll("Makan apa?", ["Nasi", "Mie"], 1);
wa.KirimReaksi("👍");
wa.Hapus(msg_id);
wa.HapusPesanOrang(msg_id, sender_participant);
wa.EditTeks(msg_id, "teks baru");
buat media_masuk = wa.UnduhMedia(m["budy"]["kutipan"]["media"], "/tmp/hasil.jpg");
```

Album (galeri swipe-able, bukan pesan terpisah):

```
wa.KirimAlbum([
    {"path": "/tmp/1.jpg", "tipe": "image", "caption": "foto pertama"},
    {"path": "/tmp/2.mp4", "tipe": "video", "caption": ""},
]);
```

Tombol & interaktif:

```
buat bt1 = wa.TombolUrl("Buka Website", "https://nd-labs.id");
buat bt2 = wa.TombolBalasanCepat("Refresh", ".ping");
buat bt3 = wa.TombolList("Pilih menu", [{"title": "Kategori A", "rows": [{"title": "Opsi 1", "rowId": ".opsi1"}]}]);
wa.KirimInteraktif("Pilih salah satu:", [bt1, bt2], "Footer", kosong, kosong);
wa.KirimTombolLokasi("Judul", "Alamat", "Isi", "Footer", [bt1], "/tmp/thumb.jpg", kosong);
```

Grup — semua method `Grup*` nerima `target` di akhir (`kosong` = grup aktif):

```
wa.GrupInfo(kosong);
wa.GrupInfo("120363012345678901");            // grup lain
wa.GrupPesertaDetail(kosong);
wa.GrupAkuAdmin(kosong);
wa.GrupPeserta(["6281234567890"], "add", kosong);
wa.GrupPeserta(["6281234567890"], "remove", kosong);
wa.GrupSetNama("Nama Baru", kosong);
wa.GrupSetDesk("Deskripsi baru", kosong);
wa.GrupKunci(benar, kosong);       // cuma admin yang bisa edit info
wa.GrupAnnounce(benar, kosong);    // cuma admin yang bisa kirim pesan
wa.GrupLink(salah, kosong);        // ambil link undangan
wa.GrupLink(benar, kosong);        // reset link undangan
wa.GrupKeluar(kosong);
wa.GrupBuat("Nama Grup Baru", ["6281234567890"]);
wa.GrupGabung("kode-dari-link-undangan");
buat daftar_grup = wa.GrupDaftar();
```

### `KirimPesan`

Satu pintu, nebak tipe pesan dari isi `content`. `target` = `kosong` (chat
aktif) atau user-id chat lain:

```
wa.KirimPesan(kosong, {text: "halo"});
wa.KirimPesan(kosong, {image: "/tmp/foto.jpg", caption: "cakep"});
wa.KirimPesan(kosong, {video: "/tmp/klip.mp4", caption: "nonton ini"});
wa.KirimPesan(kosong, {document: "/tmp/lap.pdf", fileName: "laporan.pdf", mimetype: "application/pdf"});
wa.KirimPesan(kosong, {audio: "/tmp/vn.ogg", mimetype: "audio/ogg", ptt: benar});
wa.KirimPesan(kosong, {sticker: "/tmp/stiker.webp"});
wa.KirimPesan(kosong, {location: {name: "ND-Labs", address: "Jakarta", thumb: kosong}});
wa.KirimPesan(kosong, {album: [{path: "/tmp/1.jpg", tipe: "image", caption: ""}]});
wa.KirimPesan(kosong, {poll: {name: "Makan apa?", values: ["Nasi", "Mie"], selectableCount: 1}});
wa.KirimPesan(kosong, {reaction: "👍"});
wa.KirimPesan("120363012345678901", {text: "broadcast ke grup lain"});

buat bt = wa.TombolUrl("Buka Website", "https://nd-labs.id");
wa.KirimPesan(kosong, {text: "cek link ini", buttons: [bt], footer: "ND-Labs"});

wa.KirimPesan(kosong, {text: "balesan"}, {quoted: konteks.kutip, additionalNodes: [nodeku]});
```

Key `content`: `text`/`teks`, `image`/`gambar`, `video`, `document`/`dokumen`,
`audio`, `sticker`/`stiker`, `location`/`lokasi`, `album`, `poll`,
`reaction`/`reaksi`, `buttons`/`tombol` (plus `footer`, `headerImage`).

## Presence, user, newsletter, panggilan, broadcast

Modul-modul ini nyediain pasangan `BuatNode*`/`urai_respons_*` (bukan
method siap pakai) — bikin node, kirim, tunggu balesan kalau butuh:

```
buat n = PRES.BuatNodePresenceUpdate("available", "Nama Bot");
NS.KirimAman(k["ws_id"], k["noise_socket"], EN.BcMarshal(n));

buat req_id = "cek_" + ke_teks(waktu());
buat n2 = USER.buat_node_cek_nomor(req_id, ["6281234567890"]);
NS.KirimAman(k["ws_id"], k["noise_socket"], EN.BcMarshal(n2));
buat hasil_cek = USER.urai_respons_cek_nomor(KL.TungguIq(k, req_id, 200));

buat n3 = CALL.BuatNodeTolakPanggilan("call_" + ke_teks(waktu()), kita_jid, penelepon_jid, call_id);
NS.KirimAman(k["ws_id"], k["noise_socket"], EN.BcMarshal(n3));
```

Builder yang ada: `PRES.buat_node_langganan_presence`, `PRES.buat_node_chat_presence`;
`USER.buat_node_cek_nomor`, `USER.buat_node_info_user`,
`USER.buat_node_dapatkan_foto_profil`, `USER.buat_node_daftar_blokir`,
`USER.buat_node_ubah_blokir`, `USER.buat_node_set_status`,
`USER.buat_node_pengaturan_privasi`, `USER.buat_node_set_privasi`;
`NEWS.buat_node_info_newsletter`, `NEWS.buat_node_ikuti_newsletter`,
`NEWS.buat_node_berhenti_newsletter`, `NEWS.buat_node_bisukan_newsletter`,
`NEWS.buat_node_buat_newsletter`, `NEWS.buat_node_reaksi_newsletter`;
`BC.buat_node_privasi_status`, `BC.buat_node_daftar_broadcast` (masing-masing
punya `urai_*` pasangannya).

## Media

```
buat mc_node = MEDIA.BuatNodeMediaConn(req_id);
buat isi = MEDIA.UnduhMedia(url, media_key, "image", sha256_hex, "/tmp/x.enc");
tulis_file("hasil.jpg", isi);

buat siap = MEDIA.SiapkanUpload(baca_file("foto.jpg"), "image");
buat mc = MEDIA.UraiMediaConn(respons_iq);
buat up = MEDIA.UnggahMedia(siap, "image", mc, "/tmp/x.enc");
```

Tipe: `image`, `video`, `audio`, `ptt`, `document`, `sticker`.

Retry kalau upload gagal `401` (`media_conn` kadaluarsa):

```
coba {
    up = MEDIA.UnggahMedia(siap, "image", mc, path_enc);
} tangkap (e) {
    jika _ada_potongan(ke_teks(e), "401") {
        mc = MEDIA.UraiMediaConn(KL.TungguIq(k, MEDIA.BuatNodeMediaConn(id_baru())));
        up = MEDIA.UnggahMedia(siap, "image", mc, path_enc);
    } lain {
        lempar e;
    }
}
```

## Reaksi & polling

```
buat r = SEC.BangunReaksi(chat, pengirim, msg_id, salah, "👍");
buat rh = SEC.bangun_hapus_reaksi(chat, pengirim, msg_id, salah);

buat p = SEC.BangunPoll("Makan apa?", ["Nasi", "Mie"], 1);
buat v = SEC.bangun_vote_poll(chat, kita, pembuat_poll, poll_id, salah, ["Mie"]);
buat cocok = SEC.cocokkan_hash_opsi(hash_list_dari_vote, "Mie");
```

## App state

```
buat n = AS.buat_node_ambil_patch(req_id, AS.NAMA_REGULAR, versi_terakhir, salah);
buat kol = AS.urai_koleksi_patch(respons);
untuk (buat i = 0; i < panjang(kol["patch"]); i = i + 1) {
    buat h = AS.proses_patch(kol["nama"], kol["patch"][i], hash_sekarang, ambil_kunci);
    untuk (buat j = 0; j < panjang(h["mutasi"]); j = j + 1) {
        cetak(AS.ringkas_mutasi(h["mutasi"][j]));
    }
}
```

## Protobuf

```
buat wire = PB.PbEnkodeBernama(peta_baru_dari({"conversation": "halo"}), "Message");
buat pesan = PB.PbDekodeBernama(wire);
buat cert = PB._pb_dekode_bernama_inner(bytes, "waCert_NoiseCertificate", PB._pb_skema());
```

## Isi folder

```
client.ns        alur runtime + WaApi
msgsend.ns       Signal protocol: X3DH, Double Ratchet, Sender Key
handshake.ns     Noise_XX handshake
pair_code.ns     pairing kode 8 digit
pair_success.ns  verifikasi + balesan pair-success
group.ns         kelola grup
user.ns          usync, cek nomor, profil, blokir, privasi
presence.ns      presence, chat state
media.ns         enkripsi/dekripsi media, upload/download
msgsecret.ns     reaksi & polling
notification.ns  notifikasi grup, device, prekey
newsletter.ns    channel
call.ns          panggilan masuk
broadcast.ns     privasi status, broadcast list
appstate.ns      sync app state

binary/          binary XML WhatsApp
socket/          framing + noise transport
store/           SQLite
util/            AES-GCM, AES-CBC, HKDF, HMAC-SHA512, base32, keypair
proto/           protobuf: semua skema whatsmeow
types/           JID
appstate/        app state keys, LTHash
tools/           binary Go pembantu
```

## tools/

- `keygen_identity` — identity keypair + signed prekey + signature
- `sign_identity` — tanda tangan XEdDSA
- `zlib_inflate` — dekompresi frame `w:g2`

## Catatan implementasi

- Kirim frame lewat `NS.KirimAman()`, jangan `KirimFrame`+`ws_kirim` manual
  dari lebih dari satu goroutine.
- `receipt` dan `call` wajib di-ACK juga (`MS.BuatNodeAck`), bukan cuma
  `message`/`notification`.
- Node yang masuk pas nunggu balesan `<iq>` tetep harus diproses
  (`ProsesNode`), jangan di-skip.
- `pkmsg` dipakai terus sampai `acked` di `send_sessions`, baru pindah ke
  `type="msg"`.
- Retry (`<receipt type="retry">`) pakai `msg_id`/`t` yang sama, bukan
  pesan baru.
- `ws_terima` cuma boleh dipanggil dari satu thread. IQ dari goroutine
  lain lewat `TungguIq`, jangan panggil `ws_terima` sendiri.
- `TungguIq` gak boleh dipanggil sinkron dari loop koneksi utama.
- Pastiin binary `nusa` gak punya bug lock-ordering channel+GC lama.
