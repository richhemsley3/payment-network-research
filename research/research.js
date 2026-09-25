/* the contents rail follows the reader: the section in view is the current link */
(function(){
  var links = Array.prototype.slice.call(document.querySelectorAll('.rs-contents a[href^="#"]'));
  if (!links.length || !('IntersectionObserver' in window)) return;
  var byId = {}; links.forEach(function(a){ byId[a.getAttribute('href').slice(1)] = a; });
  var current = null;
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){ if (e.isIntersecting) { if (current) current.classList.remove('is-current'); current = byId[e.target.id]; if (current) current.classList.add('is-current'); } });
  }, { rootMargin: '-10% 0px -80% 0px', threshold: 0 });
  Object.keys(byId).forEach(function(id){ var el = document.getElementById(id); if (el) io.observe(el); });
})();
