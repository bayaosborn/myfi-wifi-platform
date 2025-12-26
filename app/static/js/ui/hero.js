
async function loadHeroGreeting() {
  const titleEl = document.getElementById('heroTitle');
  const subtitleEl = document.getElementById('heroSubtitle');
  if (!titleEl) return;

  /* --------------------------
     1. Session cache
  --------------------------- */
  const cached = sessionStorage.getItem('myfi_hero');
  if (cached) {
    const data = JSON.parse(cached);
    renderHero(data, false);
    return;
  }

  try {
    const res = await fetch('/api/auth/user');
    if (!res.ok) throw new Error('Auth error');
    const user = await res.json();

    /* --------------------------
       2. Name processing
    --------------------------- */
    let rawName = user.full_name || user.username || '';
    let firstName = rawName.split(' ')[0].slice(0, 8);
    firstName =
      firstName.charAt(0).toUpperCase() +
      firstName.slice(1).toLowerCase();

    const hasName = firstName.length > 0;

    /* --------------------------
       3. Time + color logic
    --------------------------- */
    const hour = new Date().getHours();
    let greeting = 'Hello';
    let color = '#0058fc';

    if (hour >= 5 && hour < 12) {
      greeting = 'Good morning';
      color = '#0058fc';
    } else if (hour >= 12 && hour < 18) {
      greeting = 'Good afternoon';
      color = '#0058fc';
    } else {
      greeting = 'Good evening';
      color = '#f59e0b';
    }

    /* --------------------------
       4. First-time detection
    --------------------------- */
    const firstVisitKey = 'myfi_seen';
    const isFirstTime = !localStorage.getItem(firstVisitKey);
    if (isFirstTime) localStorage.setItem(firstVisitKey, '1');

    /* --------------------------
       5. Message selection
    --------------------------- */
    let titleText;

    if (isFirstTime) {
      titleText = hasName
        ? `Welcome, ${firstName}`
        : 'Welcome to Myfi';
    } else {
      const options = [];

      if (hasName) options.push(`${greeting}, ${firstName}`);
      options.push('Welcome to Myfi', 'Organize your contacts');

      titleText = options[Math.floor(Math.random() * options.length)];
    }

    /* --------------------------
       6. Subtitle (max 2/day)
    --------------------------- */
    const today = new Date().toDateString();
    const subtitleKey = `myfi_subtitle_${today}`;
    let subtitleCount = Number(localStorage.getItem(subtitleKey) || 0);

    let subtitleText = '';
    if (subtitleCount < 2 && Math.random() < 0.4) {
      subtitleText = hasName
        ? 'Everything in one place'
        : 'Simple. Fast. Secure.';

      localStorage.setItem(subtitleKey, subtitleCount + 1);
    }

    const payload = {
      titleText,
      subtitleText,
      color
    };

    sessionStorage.setItem('myfi_hero', JSON.stringify(payload));
    renderHero(payload, true);

  } catch (e) {
    renderHero({
      titleText: 'Welcome to Myfi',
      subtitleText: '',
      color: '#0058fc'
    }, true);
  }
}

/* --------------------------
   Render helper
--------------------------- */
function renderHero(data, animate) {
  const titleEl = document.getElementById('heroTitle');
  const subtitleEl = document.getElementById('heroSubtitle');

  titleEl.textContent = data.titleText;
  titleEl.style.color = data.color;

  if (data.subtitleText && subtitleEl) {
    subtitleEl.textContent = data.subtitleText;
    requestAnimationFrame(() => subtitleEl.classList.add('show'));
  }

  if (animate) {
    requestAnimationFrame(() => titleEl.classList.add('show'));
  } else {
    titleEl.classList.add('show');
    subtitleEl && subtitleEl.classList.add('show');
  }
}

document.addEventListener('DOMContentLoaded', loadHeroGreeting);
