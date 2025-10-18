# MyFi - WiFi Group Payment System

## Overview

MyFi is a Flask-based web application that enables collaborative WiFi access through group payments. Users can create or join groups, pool payments together, and gain access to WiFi credentials once payment targets are met. The system includes wallet functionality, payment verification, and comprehensive admin controls.

**Core Purpose**: Democratize WiFi access by allowing groups to share costs and collectively unlock network credentials.

**Tech Stack**:
- Backend: Flask 3.1.2 (Python)
- Database: Supabase (PostgreSQL via HTTP API)
- Frontend: Server-side rendering with Jinja2 templates
- Session Management: Flask sessions with secure cookies

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

**Blueprint-Based Routing**: The application uses Flask Blueprints to organize functionality into modular components:
- `auth` - User authentication (signup/login)
- `groups` - WiFi group creation and management
- `payments` - Payment submission and tracking
- `admin` - Administrative dashboard and controls
- `wifi` - QR code generation for WiFi access
- `admin_tools` - Database diagnostics and monitoring
- `wallet` - User wallet balance management
- `admin_wallet` - Admin wallet confirmation workflows

**Rationale**: Blueprints provide clear separation of concerns, making the codebase maintainable and allowing different features to evolve independently.

### Data Access Pattern

**Direct Supabase HTTP Client**: All database operations use the Supabase Python client library (`supabase-py`) with table-based queries:
```python
supabase.table('user').select('*').eq('id', user_id).execute()
```

**Why not SQLAlchemy**: The application was migrated from SQLAlchemy to pure Supabase client access to:
- Reduce dependency complexity
- Leverage Supabase's built-in features (RLS, real-time, auth)
- Simplify deployment without ORM configuration

**Trade-offs**: Less type safety and IDE support compared to ORM models, but gains simplicity and direct access to Supabase features.

### Authentication & Authorization

**Session-Based Auth**: Uses Flask's secure session cookies to maintain user state:
- User sessions stored in encrypted cookies
- 24-hour session lifetime
- HTTPOnly and SameSite=Lax for security

**Two-Tier Access Control**:
1. **Regular Users**: Managed via `@login_required` decorator checking `session['user_id']`
2. **Admin Users**: Managed via `@admin_required` decorator checking `session['is_admin']`

**Password Security**: Werkzeug's `generate_password_hash()` and `check_password_hash()` for bcrypt-based hashing.

### Payment & Wallet System

**Wallet-First Architecture**: Users must fund a wallet before joining groups:
- New signups create wallet with `pending` status
- Admin must manually verify M-PESA payments and approve wallets
- Once approved, wallet_balance is set to 100 KSH and status becomes `approved`

**Payment Verification Flow**:
1. User submits payment evidence (transaction code, phone number)
2. Payment stored with `verified=false`
3. Admin reviews and approves/rejects via dashboard
4. On approval, group balance increments and group may activate

**Why Manual Verification**: Avoids M-PESA API integration complexity while maintaining payment integrity through admin oversight.

### Group Lifecycle Management

**State Machine Design**: Groups transition through states:
- `pending` - Created but payment target not met
- `active` - Payment target reached, WiFi password revealed
- `expired` - Week_end date passed, access revoked

**Expiration Mechanism**: 
- Admin manually triggers `WiFiService.check_expired_groups()`
- Compares current time against `week_end` timestamp
- Batch updates expired groups and revokes password access

**Alternative Considered**: Automated cron jobs were considered but manual triggering provides more control and reduces infrastructure requirements.

### QR Code Generation

**On-Demand Generation**: WiFi credentials encoded into QR codes using the `qrcode` library:
- Generates `WIFI:S:{SSID};T:{SECURITY};P:{PASSWORD};;` format
- Rendered as base64-encoded PNG images
- Logo overlay using Pillow (PIL)

**Why Server-Side**: Keeps WiFi credentials secure (never sent to client) and provides consistent QR code quality.

### Service Layer Pattern

**Utility Services**: Business logic encapsulated in service classes:
- `AnalyticsService` - Dashboard statistics and revenue tracking
- `WiFiService` - Group expiration and activation logic

**Benefits**: Separates business logic from route handlers, enabling reuse and testing. Services directly interact with Supabase client.

## External Dependencies

### Database & Backend Services

**Supabase**: 
- PostgreSQL database hosted at `*.supabase.co`
- Accessed via REST API using `supabase-py==2.14.0`
- Connection configured via `SUPABASE_URL` and `SUPABASE_KEY` environment variables
- Tables: `user`, `group`, `member`, `payment`

**Why Supabase**: Provides managed PostgreSQL with built-in auth, real-time subscriptions, and RESTful API access without managing database servers.

### Python Dependencies

**Core Framework**:
- `Flask==3.1.2` - Web framework
- `Jinja2==3.1.6` - Template engine (bundled with Flask)
- `Werkzeug==3.1.3` - WSGI utilities and security helpers

**Production Server**:
- `gunicorn==23.0.0` - WSGI HTTP server for production deployment

**Utilities**:
- `python-dotenv==1.1.1` - Environment variable management
- `Pillow==11.3.0` - Image processing for QR code logo overlays
- `qrcode==8.2` - QR code generation

**Database Client**:
- `supabase==2.14.0` - Official Supabase Python client (upgraded from 2.3.4 to resolve httpx compatibility issues)

### Environment Configuration

**Required Environment Variables**:
- `SECRET_KEY` - Flask session encryption key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anonymous/service key
- `SSID_NAME` - WiFi network name
- `SSID_PASSWORD` - WiFi network password
- `SSID_SECURITY` - WiFi security type (default: WPA2)
- `PORT` - Application port (default: 5000)
- `ADMIN_PASSWORD` - Admin account password hash

### Frontend Assets

**Static Files**: CSS and JavaScript served from `/static/`:
- Vanilla JavaScript (no frameworks)
- Responsive CSS without preprocessors
- Modal-based authentication UI

**No Build Step**: Application serves raw CSS/JS files directly, simplifying deployment and reducing complexity.

## Recent Changes

### October 18, 2025 - Production Setup Complete
- **Dependency Upgrade**: Upgraded `supabase` from 2.3.4 to 2.14.0 to resolve httpx compatibility issues
- **File Structure**: Organized project with proper folder structure (routes/, templates/, static/, utils/)
- **Missing Assets**: Created logo.svg and 404.html template
- **Testing**: Verified all routes working (home, login, admin) with no breaking issues
- **Documentation**: Created replitlogs.md with complete activity log
- **Status**: All pages load correctly, server running on port 5000, ready for use