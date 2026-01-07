// Player Gallery Carousel
document.addEventListener('DOMContentLoaded', function() {
    const track = document.querySelector('.carousel-track');
    const slides = document.querySelectorAll('.carousel-slide');
    const prevBtn = document.querySelector('.carousel-btn--prev');
    const nextBtn = document.querySelector('.carousel-btn--next');
    const dotsContainer = document.querySelector('.carousel-dots');
    
    if (!track || slides.length === 0) return;
    
    // Add lazy loading to carousel images
    slides.forEach(slide => {
        const img = slide.querySelector('img');
        if (img) {
            img.loading = 'lazy';
            img.decoding = 'async';
        }
    });
    
    let currentIndex = 0;
    let slidesPerView = window.innerWidth <= 768 ? 1 : 3;
    const totalSlides = slides.length;
    let maxIndex = Math.max(0, totalSlides - slidesPerView);
    
    // Create dots
    if (dotsContainer) {
        const numDots = maxIndex + 1;
        for (let i = 0; i < numDots; i++) {
            const dot = document.createElement('button');
            dot.classList.add('carousel-dot');
            if (i === 0) dot.classList.add('active');
            dot.addEventListener('click', () => goToSlide(i));
            dotsContainer.appendChild(dot);
        }
    }
    
    const dots = document.querySelectorAll('.carousel-dot');
    
    function updateDots() {
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === currentIndex);
        });
    }
    
    function updateCarousel() {
        const slideWidth = slides[0].offsetWidth + 16; // 16px gap
        track.style.transform = `translateX(-${currentIndex * slideWidth}px)`;
        updateDots();
    }
    
    function goToSlide(index) {
        currentIndex = Math.max(0, Math.min(index, maxIndex));
        updateCarousel();
    }
    
    function nextSlide() {
        if (currentIndex < maxIndex) {
            currentIndex++;
        } else {
            currentIndex = 0;
        }
        updateCarousel();
    }
    
    function prevSlide() {
        if (currentIndex > 0) {
            currentIndex--;
        } else {
            currentIndex = maxIndex;
        }
        updateCarousel();
    }
    
    if (prevBtn) prevBtn.addEventListener('click', prevSlide);
    if (nextBtn) nextBtn.addEventListener('click', nextSlide);
    
    // Touch support
    let touchStartX = 0;
    let touchEndX = 0;
    
    track.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
    }, {passive: true});
    
    track.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, {passive: true});
    
    function handleSwipe() {
        const diff = touchStartX - touchEndX;
        if (Math.abs(diff) > 50) {
            if (diff > 0) nextSlide();
            else prevSlide();
        }
    }
    
    // Lightbox
    const lightbox = document.querySelector('.lightbox');
    const lightboxImg = document.querySelector('.lightbox__img');
    const lightboxClose = document.querySelector('.lightbox__close');
    const lightboxPrev = document.querySelector('.lightbox__nav--prev');
    const lightboxNext = document.querySelector('.lightbox__nav--next');
    
    let lightboxIndex = 0;
    const images = Array.from(slides).map(slide => slide.querySelector('img').src);
    
    slides.forEach((slide, index) => {
        slide.querySelector('img').addEventListener('click', () => {
            lightboxIndex = index;
            openLightbox();
        });
    });
    
    function openLightbox() {
        if (lightbox && lightboxImg) {
            lightboxImg.src = images[lightboxIndex];
            lightbox.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    function closeLightbox() {
        if (lightbox) {
            lightbox.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    function lightboxNextImg() {
        lightboxIndex = (lightboxIndex + 1) % images.length;
        lightboxImg.src = images[lightboxIndex];
    }
    
    function lightboxPrevImg() {
        lightboxIndex = (lightboxIndex - 1 + images.length) % images.length;
        lightboxImg.src = images[lightboxIndex];
    }
    
    if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
    if (lightboxPrev) lightboxPrev.addEventListener('click', lightboxPrevImg);
    if (lightboxNext) lightboxNext.addEventListener('click', lightboxNextImg);
    
    if (lightbox) {
        lightbox.addEventListener('click', e => {
            if (e.target === lightbox) closeLightbox();
        });
    }
    
    // Keyboard navigation
    document.addEventListener('keydown', e => {
        if (lightbox && lightbox.classList.contains('active')) {
            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowRight') lightboxNextImg();
            if (e.key === 'ArrowLeft') lightboxPrevImg();
        }
    });
    
    // Resize handling
    window.addEventListener('resize', () => {
        currentIndex = 0;
        updateCarousel();
    });
});
