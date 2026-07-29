const initLangAIUI = () => {
  const root = document.documentElement;
  const themeToggle = document.getElementById('themeToggle');
  const themeLabel = themeToggle ? themeToggle.querySelector('.theme-label') : null;

  const applyTheme = (theme) => {
    const resolvedTheme = theme === 'dark' ? 'dark' : 'light';
    const isDark = resolvedTheme === 'dark';

    root.setAttribute('data-theme', resolvedTheme);

    if (themeToggle) {
      themeToggle.classList.toggle('is-dark', isDark);
      themeToggle.setAttribute('aria-pressed', String(isDark));
    }

    if (themeLabel) {
      themeLabel.textContent = isDark ? 'Night' : 'Day';
    }
  };

  let savedTheme = null;
  try {
    savedTheme = localStorage.getItem('langai-theme');
  } catch (error) {
    savedTheme = null;
  }
  applyTheme(savedTheme);

  if (themeToggle) {
    const toggleTheme = () => {
      const nextTheme = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(nextTheme);
      try {
        localStorage.setItem('langai-theme', nextTheme);
      } catch (error) {
        // Ignore storage errors in private/restricted contexts.
      }
    };

    themeToggle.addEventListener('click', toggleTheme);
    themeToggle.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        toggleTheme();
      }
    });
  }

  document.querySelectorAll('.stat-value').forEach(el => {
    const target = parseInt(el.textContent.trim()) || 0;
    if (target === 0) return;
    let current = 0;
    const step = Math.ceil(target / 40);
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current.toLocaleString();
      if (current >= target) clearInterval(timer);
    }, 25);
  });
  const path = window.location.pathname.replace(/\/$/, '') || '/';
  document.querySelectorAll('.nav-pill').forEach(a => {
    const href = (a.getAttribute('href') || '').replace(/\/$/, '') || '/';
    if (href && path === href) {
      a.classList.add('active');
    } else {
      a.classList.remove('active'); // clear any server-side active if JS overrides
    }
  });
  setTimeout(() => {
    if (typeof bootstrap !== 'undefined') {
      document.querySelectorAll('.toast.show').forEach(t => {
        const inst = bootstrap.Toast.getInstance(t);
        if (inst) inst.hide();
      });
    }
  }, 5000);
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.opacity = '1';
        e.target.style.transform = 'translateY(0)';
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.stat-card, .history-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(16px)';
    el.style.transition = 'opacity .4s ease, transform .4s ease';
    observer.observe(el);
  });

  // Animate langai-cards WITHOUT hiding them (opacity stays 1, only slide-in)
  document.querySelectorAll('.langai-card').forEach(el => {
    el.style.transform = 'translateY(12px)';
    el.style.transition = 'transform .4s ease';
    observer.observe(el);
  });

};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLangAIUI);
} else {
  initLangAIUI();
}