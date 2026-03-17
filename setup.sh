#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  EduZen — O'rnatish va ishga tushirish skripti
#  Ishlatish: chmod +x setup.sh && ./setup.sh
# ═══════════════════════════════════════════════════════════════
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓] $1${NC}"; }
warn() { echo -e "${YELLOW}[!] $1${NC}"; }
err()  { echo -e "${RED}[✗] $1${NC}"; exit 1; }

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║   EduZen Backend Setup v1.0      ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# ── 1. Python tekshiruvi ──────────────────────────────────────
log "Python tekshirilmoqda..."
python3 --version || err "Python3 topilmadi"

# ── 2. Virtual muhit ─────────────────────────────────────────
if [ ! -d "venv" ]; then
    log "Virtual muhit yaratilmoqda..."
    python3 -m venv venv
fi
source venv/bin/activate
log "Virtual muhit faollashtirildi"

# ── 3. Paketlar ───────────────────────────────────────────────
log "Paketlar o'rnatilmoqda..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
log "Paketlar o'rnatildi"

# ── 4. .env fayli ─────────────────────────────────────────────
if [ ! -f ".env" ]; then
    warn ".env fayli topilmadi — .env.example dan nusxa olinmoqda"
    cp .env.example .env
    warn ">>> .env faylini to'ldiring! (nano .env)"
fi

# ── 5. MySQL bazasi ───────────────────────────────────────────
log "MySQL bazasi tekshirilmoqda..."
source .env 2>/dev/null || true
DB_NAME=${DB_NAME:-eduzen_db}
DB_USER=${DB_USER:-root}
DB_PASSWORD=${DB_PASSWORD:-""}
DB_HOST=${DB_HOST:-localhost}

mysql -u"$DB_USER" -p"$DB_PASSWORD" -h"$DB_HOST" -e \
    "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" \
    2>/dev/null && log "Baza '$DB_NAME' tayyor" || warn "Bazani qo'lda yarating: CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4;"

# ── 6. Migratsiyalar ──────────────────────────────────────────
log "Migratsiyalar ishga tushirilmoqda..."
python manage.py makemigrations users courses payments
python manage.py migrate
log "Migratsiyalar bajarildi"

# ── 7. Static fayllar ─────────────────────────────────────────
log "Static fayllar yig'ilmoqda..."
python manage.py collectstatic --noinput -v 0
log "Static fayllar tayyor"

# ── 8. Superuser ──────────────────────────────────────────────
warn "Superuser yaratish (Enter bosib o'tish mumkin):"
python manage.py createsuperuser --email admin@eduzen.uz || true

echo ""
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║   O'rnatish muvaffaqiyatli yakunlandi! 🎉            ║"
echo "  ╠══════════════════════════════════════════════════════╣"
echo "  ║  Serverni ishga tushirish:                           ║"
echo "  ║    source venv/bin/activate                         ║"
echo "  ║    python manage.py runserver                       ║"
echo "  ╠══════════════════════════════════════════════════════╣"
echo "  ║  API endpoints:                                      ║"
echo "  ║    POST  /api/v1/auth/register/                     ║"
echo "  ║    POST  /api/v1/auth/login/                        ║"
echo "  ║    GET   /api/v1/courses/                           ║"
echo "  ║    POST  /api/v1/payments/initiate/                 ║"
echo "  ║    GET   /admin/                                     ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo ""
