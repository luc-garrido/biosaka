// Biosaka - Carrossel de imagens da página inicial

const slides = [...document.querySelectorAll(".carrossel-slide")];
const pontos = [...document.querySelectorAll(".carrossel-ponto")];
const carrossel = document.querySelector(".carrossel");

let atual = 0;
let timer = null;

// Mostra o slide de número "n" (volta ao início depois do último)
function irPara(n) {
  atual = (n + slides.length) % slides.length;

  slides.forEach((s, i) => {
    s.classList.toggle("ativo", i === atual);
    s.setAttribute("aria-hidden", String(i !== atual));
  });
  pontos.forEach((p, i) => p.classList.toggle("ativo", i === atual));
}

// Troca sozinho a cada 5 segundos (desligado para quem prefere menos animação)
function iniciar() {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  parar();
  timer = setInterval(() => irPara(atual + 1), 5000);
}

function parar() {
  clearInterval(timer);
}

document.querySelector(".carrossel-anterior").onclick = () => { irPara(atual - 1); iniciar(); };
document.querySelector(".carrossel-proximo").onclick = () => { irPara(atual + 1); iniciar(); };
pontos.forEach((p, i) => p.onclick = () => { irPara(i); iniciar(); });

// Pausa enquanto o mouse ou o foco estiverem no carrossel
carrossel.addEventListener("mouseenter", parar);
carrossel.addEventListener("mouseleave", iniciar);
carrossel.addEventListener("focusin", parar);
carrossel.addEventListener("focusout", iniciar);

iniciar();
