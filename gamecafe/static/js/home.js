window.addEventListener("load", () => {
  bulmaCarousel.attach("#game-carousel", {
    slidesToScroll: 3,
    slidesToShow: 3,
    loop: true,
    autoplay: true,
    autoplaySpeed: 10000,
  });
});
