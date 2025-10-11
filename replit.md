# WiFi QR Connect - MyFi

## Overview

MyFi is a Flask-based web application that enables WiFi access through a group payment system. Users can create or join payment groups, contribute to reach a target amount, and receive WiFi credentials via QR code once the payment goal is met. The application combines WiFi credential management with a collaborative payment model, allowing multiple users to pool resources for internet access.

## Recent Fixes (October 11, 2025)

Fixed 7 critical issues that prevented the app from running:
1. Restructured project with proper templates/ and static/ folders
2. Fixed database import bug in accounts.py
3. Cleaned up requirements.txt duplicates and added flask-sqlalchemy
4. Fixed critical route ordering bug where routes were defined after app.run()
5. Installed Python 3.11 and all dependencies
6. Configured Flask Server workflow
7. Added .gitignore for Python projects

All functionality is now working correctly. See fixed.md for detailed documentation.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture

**Framework: Flask with SQLAlchemy ORM**
- **Problem**: Need a lightweight web framework for rapid development with database integration
- **Solution**: Flask serves as the main application framework with Flask-SQLAlchemy for database operations
- **Rationale**: Flask's simplicity and extensive ecosystem make it ideal for this moderate-complexity application
- **Pros**: Easy to set up, minimal boilerplate, good community support
- **Cons**: Manual configuration required for larger applications

**Blueprint Pattern for Modular Routes**
- **Problem**: Need to organize routes and maintain clean code structure
- **Solution**: Accounts functionality separated into `accounts.py` blueprint
- **Rationale**: Blueprints enable modular organization and scalability as features grow
- **Pros**: Better code organization, easier testing, reusable components
- **Cons**: Slight overhead for simple applications

**Database Models Design**
- Core entities: Group, Member, Payment, WiFiCredential
- **Group Model**: Manages collective payment targets with fields for balance tracking, discount application, and time-based access control (week_start, week_end)
- **Member Model**: Tracks individual participants linked to groups
- **Payment Model**: Records transactions with M-Pesa code verification support
- **WiFiCredential Model**: Manages network credentials with time-based validity

**Relational Data Structure**
- One-to-many relationship: Group → Members
- One-to-many relationship: Group → Payments
- One-to-many relationship: Member → Payments
- **Rationale**: Relational model supports group-based payment tracking and credential access control

### Frontend Architecture

**Template Engine: Jinja2**
- Server-side rendered HTML templates
- Three main views:
  - `index.html`: QR code generation and display
  - `join_group.html`: Group creation and joining interface
  - `groups.html`: Groups listing view

**Client-Side Logic**
- Vanilla JavaScript for form handling
- Async fetch API for backend communication
- QR code display with Base64 encoded images

### Data Storage

**Database: SQLite**
- **Problem**: Need persistent storage for groups, members, and payment records
- **Solution**: SQLite database (`myfi.db`) with Flask-SQLAlchemy ORM
- **Rationale**: Lightweight, serverless database suitable for small to medium-scale deployments
- **Pros**: Zero configuration, file-based, ACID compliant
- **Cons**: Limited concurrent write performance, not ideal for high-traffic production

**Database Initialization**
- Tables created automatically on application startup using `db.create_all()`
- Schema managed through SQLAlchemy models

### Authentication & Authorization

**WiFi Access Control**
- Time-based validity using `week_start` and `week_end` fields
- Group status tracking (pending/active/expired)
- Password reveal controlled by `password_revealed` flag
- Payment threshold enforcement via `target_amount` vs `current_balance`

**Group Access**
- Group code-based joining system
- No user authentication implemented (open access model)
- Member identity tracked by name and phone number

### QR Code Generation

**Library: qrcode + Pillow**
- **Problem**: Need to encode WiFi credentials in scannable format
- **Solution**: Generate QR codes using WiFi configuration string format (`WIFI:T:{security};S:{ssid};P:{password};;`)
- **Implementation**: 
  - QR code generated server-side
  - Converted to Base64 PNG for browser display
  - Embedded directly in HTML template

## External Dependencies

### Python Libraries
- **Flask**: Web application framework
- **Flask-SQLAlchemy**: ORM for database operations
- **qrcode**: QR code generation
- **Pillow**: Image processing library (required by qrcode)

### Payment Integration (Placeholder)
- **M-Pesa Integration**: Referenced in Payment model (`mpesa_code` field) but not yet implemented
- Verification system (`verified` field) prepared for payment validation

### WiFi Network
- Hardcoded credentials in `app.py`:
  - SSID: "poaA7rgIU"
  - Password: "b8K!p2Zr#V7m"
  - Security: WPA
- No dynamic credential rotation implemented

### Database
- **SQLite**: File-based relational database
- **Location**: `myfi.db` in application root
- No external database server required

### Future Integration Points
- Payment gateway API (M-Pesa or similar)
- SMS notification service (for group updates)
- WiFi router API (for dynamic credential management)