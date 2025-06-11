# 🌐 Domain Setup Guide: cvlatex.zapto.org

## ✅ **Your Domain Configuration**

**Domain**: `cvlatex.zapto.org`  
**Type**: Free Dynamic DNS (Zapto.org)  
**Status**: Ready for setup! 🎉  

## 🚀 **Quick Setup Methods**

### **Option 1: Cloudflare Tunnel (Recommended) - FREE SSL**

**Benefits**: Free SSL, DDoS protection, no port forwarding, hides your IP

#### **Step 1: Install Cloudflared**
```bash
# Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
# For Windows: Download the .exe file
```

#### **Step 2: Create and Configure Tunnel**
```bash
# 1. Login to Cloudflare
cloudflared tunnel login

# 2. Create tunnel
cloudflared tunnel create cvlatex

# 3. Configure DNS (point cvlatex.zapto.org to tunnel)
cloudflared tunnel route dns cvlatex cvlatex.zapto.org

# 4. Copy tunnel credentials to your project
# Copy the tunnel ID and credentials file path to cloudflare-tunnel.yml
```

#### **Step 3: Update Configuration**
Edit `cloudflare-tunnel.yml` and replace:
- `your-tunnel-id` with your actual tunnel ID
- `/path/to/tunnel/credentials.json` with actual path

#### **Step 4: Start Everything**
```bash
# Terminal 1: Start your CVLatex server
python start_production.py

# Terminal 2: Start Cloudflare tunnel
cloudflared tunnel run cvlatex
```

#### **Step 5: Access Your Site**
- **Main Site**: https://cvlatex.zapto.org
- **Admin Panel**: https://admin.cvlatex.zapto.org
- **API**: https://api.cvlatex.zapto.org

---

### **Option 2: Port Forwarding (Traditional Method)**

#### **Step 1: Configure Router Port Forwarding**
```
Router Settings:
- External Port: 80 (HTTP) or 443 (HTTPS)
- Internal Port: 8000 (your app port)
- Internal IP: Your PC's local IP (find with: ipconfig)
- Protocol: TCP
```

#### **Step 2: Update Zapto DNS**
1. **Login to Zapto.org**
2. **Update A Record**: Point `cvlatex.zapto.org` to your public IP
3. **Set up Dynamic Updates**: Install Zapto's update client

#### **Step 3: Start Server**
```bash
python start_production.py
```

#### **Step 4: Access Your Site**
- **HTTP**: http://cvlatex.zapto.org:8000
- **Configure SSL separately if needed**

---

## 🛠️ **Production Setup Commands**

### **Complete Setup Script**
Create `start_domain_server.bat`:
```batch
@echo off
title CVLatex - cvlatex.zapto.org
echo Starting CVLatex for cvlatex.zapto.org...

cd /d "D:\CVLatex"

echo [1] Starting Production Server...
start "CVLatex Server" python start_production.py

timeout /t 5

echo [2] Starting Cloudflare Tunnel...
start "Cloudflare Tunnel" cloudflared tunnel run cvlatex

echo.
echo ✅ CVLatex is now running at:
echo 🌐 https://cvlatex.zapto.org
echo 📊 Admin: https://admin.cvlatex.zapto.org
echo.
echo Press any key to stop services...
pause

echo Stopping services...
taskkill /F /IM python.exe
taskkill /F /IM cloudflared.exe
```

### **Monitor Your Service**
```bash
# Check system status
python monitor.py --status

# Start continuous monitoring
python monitor.py
```

---

## 🔒 **Security Configuration**

### **Production Environment Variables**
Create `.env` file:
```env
# Production settings for cvlatex.zapto.org
SECRET_KEY=your-super-secret-key-change-this
HOST=0.0.0.0
PORT=8000
FLASK_ENV=production
FLASK_DEBUG=0

# Domain settings
DOMAIN=cvlatex.zapto.org
SSL_ENABLED=true
```

### **Firewall Configuration**
```bash
# Windows Firewall - Allow CVLatex
netsh advfirewall firewall add rule name="CVLatex HTTP" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="CVLatex HTTPS" dir=in action=allow protocol=TCP localport=443
```

---

## 📊 **Testing Your Setup**

### **Local Testing**
```bash
# Test local server
curl http://localhost:8000

# Test production config
python -c "from production_config import ProductionConfig; print('✅ Config loaded successfully')"
```

### **Domain Testing**
```bash
# Test domain resolution
nslookup cvlatex.zapto.org

# Test HTTP response
curl -I http://cvlatex.zapto.org

# Test HTTPS (if using Cloudflare)
curl -I https://cvlatex.zapto.org
```

### **LaTeX Testing**
```bash
# Test LaTeX functionality
python -c "
import shutil
print('✅ pdflatex available:' if shutil.which('pdflatex') else '❌ pdflatex missing:', shutil.which('pdflatex'))
"
```

---

## 🎯 **Quick Start (Recommended)**

```bash
# 1. Start production server
python start_production.py

# 2. In another terminal, test locally first
curl http://localhost:8000

# 3. Set up Cloudflare tunnel
cloudflared tunnel create cvlatex
cloudflared tunnel route dns cvlatex cvlatex.zapto.org

# 4. Start tunnel
cloudflared tunnel run cvlatex

# 5. Test your domain
# Visit: https://cvlatex.zapto.org
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

**Domain not resolving:**
- Check DNS propagation (can take up to 24 hours)
- Verify Zapto.org settings
- Test with: `nslookup cvlatex.zapto.org`

**Server not responding:**
- Ensure server is running: `python start_production.py`
- Check Windows Firewall settings
- Verify port 8000 is open

**LaTeX not working:**
- Your MiKTeX is already working perfectly! ✅
- MiKTeX-pdfTeX 4.18 (MiKTeX 24.1) detected

**SSL issues:**
- Use Cloudflare Tunnel for automatic SSL
- Cloudflare provides free SSL certificates

### **Support Commands**
```bash
# System diagnostics
python monitor.py --status

# App health check
curl http://localhost:8000/debug/system

# Check LaTeX
python -c "import shutil; print(shutil.which('pdflatex'))"
```

---

## 🎉 **Final Result**

Once configured, you'll have:

✅ **Professional Domain**: https://cvlatex.zapto.org  
✅ **Free SSL Certificate**: Secure HTTPS  
✅ **Perfect LaTeX**: MiKTeX working flawlessly  
✅ **Production Ready**: Secure configuration  
✅ **Monitoring**: System health tracking  
✅ **Admin Panel**: https://admin.cvlatex.zapto.org  

**Total Cost**: FREE! (Domain, SSL, hosting all free) 🎉

---

Your CVLatex application will be professionally hosted at **https://cvlatex.zapto.org** with full LaTeX functionality! 🚀 