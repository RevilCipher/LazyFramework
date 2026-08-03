#!/bin/bash
# ================================================
# LazyFramework Debian Package Builder (Lengkap)
# ================================================

set -e

NAME="lazyframework"
VERSION="1.0.1"
ARCH="amd64"
#PKG_DIR="${NAME}_${VERSION}_${ARCH}"
PKG_DIR="${NAME}_${VERSION}_${ARCH}"

echo "[+] Membersihkan package lama..."
rm -rf "$PKG_DIR" *.deb

echo "[+] Membuat struktur package..."
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/share/lazyframework"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"

# ====================== COPY FILES ======================
echo "[+] Menyalin file aplikasi..."
cp -r bin core modules widgets "$PKG_DIR/usr/share/lazyframework/" 2>/dev/null || true
cp gui.py lzfconsole config.json "$PKG_DIR/usr/share/lazyframework/" 2>/dev/null || true

# ====================== ENTRY POINT ======================
echo "[+] Membuat entry point /usr/bin/lzfconsole..."
cat > "$PKG_DIR/usr/bin/lzfconsole" << 'EOF'
#!/bin/bash
cd /usr/share/lazyframework
if [[ "$1" == "--gui" ]] || [[ -z "$1" && ! -t 0 ]]; then
    exec python3 gui.py "$@"
else
    exec python3 lzfconsole "$@"
fi
EOF
chmod +x "$PKG_DIR/usr/bin/lzfconsole"

# ====================== DESKTOP ENTRY ======================
echo "[+] Membuat desktop entry..."
cat > "$PKG_DIR/usr/share/applications/lazyframework.desktop" << EOF
[Desktop Entry]
Name=LazyFramework
Comment=Penetration Testing Framework
Exec=lzfconsole --gui
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Security;Development;
StartupNotify=true
EOF

# ====================== DEBIAN CONTROL FILES ======================
echo "[+] Membuat control files..."

# control
cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: $NAME
Version: $VERSION
Architecture: $ARCH
Maintainer: LazyFramework <redteamsectorid@gmail.com>
Depends: python3 (>= 3.10), python3-pip, python3-pyqt6
Description: LazyFramework - Advanced Penetration Testing Framework
 Modern GUI + CLI pentest framework with session management,
 reverse shell, and AI assistant.
Homepage: https://github.com/breachcipher/Lazy-Framework
EOF

# postinst
cat > "$PKG_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/sh
set -e
chmod +x /usr/bin/lzfconsole
echo "========================================"
echo "✅ LazyFramework berhasil diinstal!"
echo "========================================"
echo "Jalankan dengan:"
echo "   lzfconsole       → Console Mode"
echo "   lazyframework    → GUI Mode"
echo "========================================"
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# postrm (penting untuk purge bersih)
cat > "$PKG_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/sh
set -e

if [ "$1" = "purge" ]; then
    echo "[*] Menghapus semua data LazyFramework..."
    rm -rf /usr/share/lazyframework
    rm -f /usr/bin/lzfconsole
    rm -f /usr/share/applications/lazyframework.desktop
    echo "✅ LazyFramework telah dihapus sepenuhnya."
fi
EOF

# ====================== FIX PERMISSIONS ======================
# Set DEBIAN directory permissions first
chmod 755 "$PKG_DIR/DEBIAN"

# Set maintainer scripts to executable (MUST be 755)
chmod 755 "$PKG_DIR/DEBIAN/control"
chmod 755 "$PKG_DIR/DEBIAN/postinst"
chmod 755 "$PKG_DIR/DEBIAN/postrm"

# Set directory permissions
find "$PKG_DIR/usr" -type d -exec chmod 755 {} +

# Set file permissions (regular files to 644)
find "$PKG_DIR/usr" -type f -exec chmod 644 {} +

# Make binaries and scripts executable
chmod 755 "$PKG_DIR/usr/bin/lzfconsole"
chmod 755 "$PKG_DIR/usr/share/lazyframework/lzfconsole" 2>/dev/null || true
chmod 755 "$PKG_DIR/usr/share/lazyframework/gui.py" 2>/dev/null || true
# ====================== BUILD PACKAGE ======================
echo "[+] Membuat package .deb..."
dpkg-deb --build --root-owner-group "$PKG_DIR"

echo "=================================================="
echo "✅ Package BERHASIL dibuat: ${PKG_DIR}.deb"
echo "=================================================="
ls -lh "${PKG_DIR}.deb"
echo ""
echo "Install dengan:"
echo "   sudo dpkg -i ${PKG_DIR}.deb"
echo "   sudo apt install -f" apakah ini duplikat atau make file nya