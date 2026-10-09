document.addEventListener("DOMContentLoaded", function () {
  // Dark mode toggle
  var themeBtn = document.getElementById("themeToggleBtn");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var isDark = document.documentElement.getAttribute("data-theme") === "dark";
      if (isDark) {
        document.documentElement.removeAttribute("data-theme");
        localStorage.setItem("propverify-theme", "light");
      } else {
        document.documentElement.setAttribute("data-theme", "dark");
        localStorage.setItem("propverify-theme", "dark");
      }
    });
  }

  // Auto-dismiss flash alerts after a few seconds
  document.querySelectorAll(".alert").forEach(function (alertEl) {
    setTimeout(function () {
      var bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
      bsAlert.close();
    }, 6000);
  });

  // Post-login splash: overlay is rendered server-side when ?splash=1 is
  // present. Let the stamp animation play, then fade the overlay away and
  // clean the URL so a refresh doesn't replay it.
  var splash = document.getElementById("splash-overlay");
  if (splash) {
    setTimeout(function () {
      splash.classList.add("splash-hide");
      document.body.classList.remove("splash-active");
    }, 1400);

    setTimeout(function () {
      splash.remove();
      if (window.history && window.history.replaceState) {
        var url = new URL(window.location.href);
        url.searchParams.delete("splash");
        window.history.replaceState({}, document.title, url.pathname + url.search + url.hash);
      }
    }, 1900);
  }

  // Scroll-reveal: fade/slide in any .reveal-on-scroll element as it enters
  // the viewport. Falls back to showing everything immediately if
  // IntersectionObserver isn't available.
  var revealTargets = document.querySelectorAll(".reveal-on-scroll");
  if (revealTargets.length) {
    if ("IntersectionObserver" in window) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15 });
      revealTargets.forEach(function (el) { observer.observe(el); });
    } else {
      revealTargets.forEach(function (el) { el.classList.add("in-view"); });
    }
  }

  // Animated number counters: any element with data-counter="123" counts
  // up from 0 to that value once it's visible. Used on the admin dashboard
  // stat tiles and the risk score.
  var counters = document.querySelectorAll("[data-counter]");
  if (counters.length) {
    var animateCounter = function (el) {
      var target = parseFloat(el.dataset.counter);
      if (isNaN(target)) return;
      var duration = 900;
      var start = null;
      var step = function (timestamp) {
        if (!start) start = timestamp;
        var progress = Math.min((timestamp - start) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        var value = Math.round(eased * target);
        el.textContent = value + (el.dataset.counterSuffix || "");
        if (progress < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    if ("IntersectionObserver" in window) {
      var counterObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            counterObserver.unobserve(entry.target);
          }
        });
      }, { threshold: 0.4 });
      counters.forEach(function (el) { counterObserver.observe(el); });
    } else {
      counters.forEach(animateCounter);
    }
  }

  // Initialize Bootstrap tooltips (used for the "why was this flagged?"
  // explanations on each risk finding). Re-run after any dynamically
  // revealed content via a small delay isn't needed here since findings
  // are present in the initial server-rendered HTML.
  if (window.bootstrap && window.bootstrap.Tooltip) {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
      new bootstrap.Tooltip(el);
    });
  }

  // Live staged progress animation for "Run Automated Verification":
  // purely cosmetic (the real work happens server-side in one request),
  // but shows the person the AI pipeline's actual stages rather than a
  // button that looks frozen for however long the request takes.
  document.querySelectorAll("form[data-stages]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (form.dataset.submitting) return; // let the real (second) submit through
      e.preventDefault();
      form.dataset.submitting = "1";

      var btn = form.querySelector("button[type=submit]");
      var label = btn ? btn.querySelector(".btn-label") : null;
      var stages = form.dataset.stages.split("|");
      if (btn) btn.disabled = true;

      var i = 0;
      var showStage = function () {
        if (label) {
          label.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span>' + stages[i];
        }
        i++;
        if (i < stages.length) {
          setTimeout(showStage, 550);
        } else {
          setTimeout(function () { form.submit(); }, 550);
        }
      };
      showStage();
    });
  });

  // Skeleton shimmer while real photos load over the network.
  document.querySelectorAll("img.lazy-photo").forEach(function (img) {
    if (img.complete && img.naturalWidth > 0) return; // already cached/loaded
    img.classList.add("img-loading");
    var clear = function () { img.classList.remove("img-loading"); };
    img.addEventListener("load", clear, { once: true });
    img.addEventListener("error", clear, { once: true });
  });

  // Form micro-interaction: pulse a required field green when it's left
  // filled in with a valid value. Delegated at document level with
  // capture:true since blur doesn't bubble.
  document.addEventListener("blur", function (e) {
    var el = e.target;
    if (!el.matches || !el.matches(".form-control[required], .form-select[required]")) return;
    if (el.checkValidity && el.checkValidity() && String(el.value).trim() !== "") {
      el.classList.remove("input-success");
      void el.offsetWidth; // force reflow so the animation restarts on repeat blurs
      el.classList.add("input-success");
    }
  }, true);

  // Stagger delay: any group of elements with .stagger-in get an
  // incrementally increasing animation-delay so they cascade in rather
  // than popping simultaneously.
  document.querySelectorAll("[data-stagger-group]").forEach(function (group) {
    var items = group.querySelectorAll(".stagger-in, .finding-row.stagger");
    items.forEach(function (el, i) {
      el.style.animationDelay = (i * 0.08) + "s";
    });
  });

  // ----------------------------------------------------------------------
  // Landing Page Motion Graphics Canvas & Interactive Particle Web
  // ----------------------------------------------------------------------
  var heroCanvas = document.getElementById("heroMotionCanvas");
  if (heroCanvas) {
    (function () {
      var ctx = heroCanvas.getContext("2d");
      var width, height;
      var particles = [];
      var mouse = { x: null, y: null, maxDist: 120 };

      var resize = function () {
        var rect = heroCanvas.parentElement.getBoundingClientRect();
        width = heroCanvas.width = rect.width;
        height = heroCanvas.height = rect.height;
      };
      resize();
      window.addEventListener("resize", resize);

      heroCanvas.parentElement.addEventListener("mousemove", function (e) {
        var rect = heroCanvas.getBoundingClientRect();
        mouse.x = e.clientX - rect.left;
        mouse.y = e.clientY - rect.top;
      });

      heroCanvas.parentElement.addEventListener("mouseleave", function () {
        mouse.x = null;
        mouse.y = null;
      });

      var numParticles = Math.min(Math.floor((width * height) / 12000), 55);
      numParticles = Math.max(numParticles, 24);

      for (var i = 0; i < numParticles; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.75,
          vy: (Math.random() - 0.5) * 0.75,
          radius: Math.random() * 2.2 + 1.2,
          color: Math.random() > 0.4 ? "rgba(45, 212, 206," : (Math.random() > 0.5 ? "rgba(225, 168, 61," : "rgba(255, 255, 255,")
        });
      }

      var animate = function () {
        ctx.clearRect(0, 0, width, height);

        // Update & Draw particles
        for (var i = 0; i < particles.length; i++) {
          var p = particles[i];
          p.x += p.vx;
          p.y += p.vy;

          if (p.x < 0 || p.x > width) p.vx *= -1;
          if (p.y < 0 || p.y > height) p.vy *= -1;

          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
          ctx.fillStyle = p.color + "0.65)";
          ctx.fill();

          // Connect particles near each other (cadastral mesh graph)
          for (var j = i + 1; j < particles.length; j++) {
            var p2 = particles[j];
            var dx = p.x - p2.x;
            var dy = p.y - p2.y;
            var dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < 110) {
              var alpha = (1 - dist / 110) * 0.28;
              ctx.beginPath();
              ctx.moveTo(p.x, p.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.strokeStyle = "rgba(255, 255, 255, " + alpha + ")";
              ctx.lineWidth = 0.85;
              ctx.stroke();
            }
          }

          // Interactive mouse connection
          if (mouse.x !== null && mouse.y !== null) {
            var mdx = p.x - mouse.x;
            var mdy = p.y - mouse.y;
            var mdist = Math.sqrt(mdx * mdx + mdy * mdy);
            if (mdist < mouse.maxDist) {
              var mAlpha = (1 - mdist / mouse.maxDist) * 0.55;
              ctx.beginPath();
              ctx.moveTo(p.x, p.y);
              ctx.lineTo(mouse.x, mouse.y);
              ctx.strokeStyle = "rgba(45, 212, 206, " + mAlpha + ")";
              ctx.lineWidth = 1.2;
              ctx.stroke();
            }
          }
        }

        requestAnimationFrame(animate);
      };
      animate();
    })();
  }

  // Interactive 3D tilt on hero graphic scanner
  var graphicCard = document.querySelector(".hero-graphic-card");
  var scannerScreen = document.querySelector(".verification-scanner-screen");
  if (graphicCard && scannerScreen) {
    graphicCard.addEventListener("mousemove", function (e) {
      var rect = graphicCard.getBoundingClientRect();
      var x = e.clientX - rect.left;
      var y = e.clientY - rect.top;
      var centerX = rect.width / 2;
      var centerY = rect.height / 2;
      var rotateX = ((y - centerY) / centerY) * -10;
      var rotateY = ((x - centerX) / centerX) * 10;
      scannerScreen.style.transform = "perspective(1000px) rotateX(" + rotateX + "deg) rotateY(" + rotateY + "deg) translateY(-2px)";
    });

    graphicCard.addEventListener("mouseleave", function () {
      scannerScreen.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)";
    });
  }
  // ----------------------------------------------------------------------
  // Sitewide Ambient Backdrop Motion Canvas
  // ----------------------------------------------------------------------
  var ambientCanvas = document.getElementById("ambientBackdropCanvas");
  if (ambientCanvas) {
    (function () {
      var ctx = ambientCanvas.getContext("2d");
      var w, h;
      var points = [];

      var onResize = function () {
        w = ambientCanvas.width = window.innerWidth;
        h = ambientCanvas.height = window.innerHeight;
      };
      onResize();
      window.addEventListener("resize", onResize);

      // Create gentle floating holographic cadastral nodes
      var count = Math.min(Math.floor((window.innerWidth * window.innerHeight) / 22000), 38);
      count = Math.max(count, 18);

      for (var i = 0; i < count; i++) {
        points.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.45,
          vy: (Math.random() - 0.5) * 0.45,
          radius: Math.random() * 2 + 1,
          baseAlpha: Math.random() * 0.35 + 0.15,
          type: Math.random() > 0.5 ? "teal" : (Math.random() > 0.5 ? "gold" : "cyan")
        });
      }

      var drawAmbient = function () {
        ctx.clearRect(0, 0, w, h);
        var isDark = document.documentElement.getAttribute("data-theme") === "dark";

        for (var i = 0; i < points.length; i++) {
          var pt = points[i];
          pt.x += pt.vx;
          pt.y += pt.vy;

          if (pt.x < 0) pt.x = w;
          if (pt.x > w) pt.x = 0;
          if (pt.y < 0) pt.y = h;
          if (pt.y > h) pt.y = 0;

          var colorStr;
          if (pt.type === "teal") {
            colorStr = isDark ? "rgba(45, 212, 206, " : "rgba(14, 165, 163, ";
          } else if (pt.type === "gold") {
            colorStr = isDark ? "rgba(240, 194, 114, " : "rgba(225, 168, 61, ";
          } else {
            colorStr = isDark ? "rgba(147, 197, 253, " : "rgba(56, 189, 248, ";
          }

          ctx.beginPath();
          ctx.arc(pt.x, pt.y, pt.radius, 0, Math.PI * 2);
          ctx.fillStyle = colorStr + (isDark ? pt.baseAlpha * 0.8 : pt.baseAlpha * 1.2) + ")";
          ctx.fill();

          // Delicate connecting lines
          for (var j = i + 1; j < points.length; j++) {
            var pt2 = points[j];
            var dx = pt.x - pt2.x;
            var dy = pt.y - pt2.y;
            var dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < 130) {
              var lineAlpha = (1 - dist / 130) * (isDark ? 0.12 : 0.18);
              ctx.beginPath();
              ctx.moveTo(pt.x, pt.y);
              ctx.lineTo(pt2.x, pt2.y);
              ctx.strokeStyle = colorStr + lineAlpha + ")";
              ctx.lineWidth = 0.75;
              ctx.stroke();
            }
          }
        }

        requestAnimationFrame(drawAmbient);
      };
      drawAmbient();
    })();
  }
});
