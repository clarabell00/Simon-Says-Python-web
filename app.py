import random
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'arcade_simon_says_secret_key'  

PILIHAN_WARNA = ['red', 'yellow', 'green', 'blue']
pola_game = []
score_game = 0
best_score = 0
waktu_ingat = 5.0


# --- FUNGSI LOGIKA BAKU PYTHON ---

def reset_game():
    """Memulai ulang game dan mengacak 4 pola warna pertama"""
    global pola_game, score_game, waktu_ingat
    score_game = 0
    waktu_ingat = 5.0
    pola_game = [random.choice(PILIHAN_WARNA) for _ in range(4)]
    return pola_game


def tambah_pola_baru():
    """Mengacak ulang 4 pola warna baru secara penuh per ronde"""
    global pola_game, waktu_ingat
    pola_game = [random.choice(PILIHAN_WARNA) for _ in range(4)]
    waktu_ingat = max(1.0, waktu_ingat - 0.5)


def cek_jawaban_user(jawaban_player):
    """Mengecek susunan warna dari JS/HTML dengan pola Python"""
    global score_game, best_score, pola_game, waktu_ingat
    
    if jawaban_player == pola_game:
        score_game += 10
        
        # Update Best Score jika skor melampaui rekor
        if score_game > best_score:
            best_score = score_game
            
        tambah_pola_baru()
        return {
            "status": "BENAR",
            "score": score_game,
            "best_score": best_score,
            "ronde": len(pola_game),
            "waktu": waktu_ingat,
            "pola_baru": pola_game
        }
    else:
        return {
            "status": "GAME_OVER",
            "score_akhir": score_game,
            "best_score": best_score,
            "kunci_jawaban": pola_game  
        }


# --- ROUTING FLASK (NAVIGASI HALAMAN HTML) ---

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/cara-bermain')
def halaman_cara_bermain():
    ronde_saat_ini = 1
    
    # Ambil nilai skor terakhir dan best score dari session (default dari global jika belum ada)
    last_score = session.get('last_score', score_game)
    session_best = session.get('best_score', best_score)
    
    return render_template(
        'mulai.html',  
        score=last_score, 
        best_score=session_best, 
        ronde=ronde_saat_ini
    )


@app.route('/game')
def area_game():
    return render_template('ingame.html')


@app.route('/gameover')
def game_over():
    global best_score, score_game
    
    # Ambil nilai score dan kunci jawaban dari URL query parameter
    current_score = request.args.get('score', score_game, type=int)
    kunci_raw = request.args.get('kunci', '')  # Contoh string raw: "red,yellow,green,blue"
    
    # Simpan skor sesi terakhir ke Flask session
    session['last_score'] = current_score
    
    # Kelola best score melalui Flask session & global
    session_best = session.get('best_score', best_score)
    if current_score > session_best:
        session_best = current_score
        session['best_score'] = session_best
        best_score = session_best
        
    return render_template(
        'gameover.html', 
        score=current_score, 
        best_score=session_best, 
        kunci_raw=kunci_raw
    )


# --- ROUTING API (DIPANGGIL JAVASCRIPT/FETCH) ---

@app.route('/start', methods=['POST'])
def start_game():
    pola_awal = reset_game()
    session_best = session.get('best_score', best_score)
    return jsonify({
        "pola": pola_awal,
        "kunci_jawaban": pola_awal,
        "waktu": waktu_ingat,
        "score": score_game,
        "best_score": session_best,
        "ronde": 1
    })


@app.route('/tebak', methods=['POST'])
def proses_tebakan():
    data = request.get_json()
    jawaban_player = data.get('jawaban', [])
    hasil = cek_jawaban_user(jawaban_player)
    
    # Update session jika ada skor baru / best score baru dari API
    if hasil.get('status') == 'BENAR':
        session['last_score'] = hasil['score']
        if hasil['best_score'] > session.get('best_score', 0):
            session['best_score'] = hasil['best_score']
            
    return jsonify(hasil)


if __name__ == '__main__':
    app.run(debug=True)