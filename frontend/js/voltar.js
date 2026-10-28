// Biosaka - Botão de voltar
// Leva à página anterior do histórico do navegador.
// Se não houver página anterior (ex.: o link foi aberto direto), segue o href do botão.

document.querySelectorAll("[data-voltar]").forEach(botao => {
  botao.addEventListener("click", e => {
    if (history.length > 1) {
      e.preventDefault();
      history.back();
    }
  });
});
