(function () {
  function initMobileNav() {
    var header = document.querySelector("header.header");
    if (!header || header.querySelector(".nav-toggle")) return;

    var nav = header.querySelector("nav.nav");
    if (!nav) return;

    var links = [];
    nav.querySelectorAll(".nav-left a, .nav-right a").forEach(function (link) {
      if (!link || !link.textContent) return;
      links.push({
        href: link.getAttribute("href") || "#",
        text: link.textContent.trim(),
        onclick: link.getAttribute("onclick"),
        active: link.classList.contains("active")
      });
    });

    if (!links.length) return;

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "nav-toggle";
    btn.setAttribute("aria-label", "Открыть меню");
    btn.setAttribute("aria-expanded", "false");
    btn.innerHTML = "<span></span><span></span><span></span>";

    var drawer = document.createElement("div");
    drawer.className = "mobile-drawer";
    drawer.setAttribute("role", "navigation");

    links.forEach(function (item) {
      var a = document.createElement("a");
      a.href = item.href || "#";
      a.textContent = item.text;
      if (item.active) a.classList.add("active");
      if (item.onclick) a.setAttribute("onclick", item.onclick);
      a.addEventListener("click", function () {
        setOpen(false);
      });
      drawer.appendChild(a);
    });

    header.appendChild(btn);
    header.appendChild(drawer);

    function setOpen(open) {
      header.classList.toggle("nav-open", open);
      document.body.classList.toggle("nav-lock", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.setAttribute("aria-label", open ? "Закрыть меню" : "Открыть меню");
    }

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      setOpen(!header.classList.contains("nav-open"));
    });

    document.addEventListener("click", function (e) {
      if (!header.contains(e.target)) setOpen(false);
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 900) setOpen(false);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMobileNav);
  } else {
    initMobileNav();
  }
})();
