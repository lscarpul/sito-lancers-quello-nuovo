/* ===================================
   LANCERS BASEBALL CLUB - JAVASCRIPT
   =================================== */

document.addEventListener('DOMContentLoaded', function() {
    // ===================================
    // PRELOADER
    // ===================================
    const preloader = document.getElementById('preloader');
    if (preloader) {
        window.addEventListener('load', function() {
            setTimeout(() => {
                preloader.classList.add('hidden');
            }, 500);
        });
    }

    // ===================================
    // HEADER SCROLL EFFECT
    // ===================================
    const header = document.getElementById('header');
    let lastScroll = 0;

    function handleScroll() {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }

        lastScroll = currentScroll;
    }

    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Check on load

    // ===================================
    // MOBILE NAVIGATION
    // ===================================
    const navToggle = document.getElementById('nav-toggle');
    const navClose = document.getElementById('nav-close');
    const navMenu = document.getElementById('nav-menu');

    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.add('show-menu');
            document.body.style.overflow = 'hidden';
        });
    }

    if (navClose) {
        navClose.addEventListener('click', () => {
            navMenu.classList.remove('show-menu');
            document.body.style.overflow = '';
        });
    }

    // Close menu when clicking on a link
    const navLinks = document.querySelectorAll('.nav__link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('show-menu');
            document.body.style.overflow = '';
        });
    });

    // Mobile dropdown toggle
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        const link = dropdown.querySelector('.nav__link');
        link.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                dropdown.classList.toggle('active');
            }
        });
    });

    // ===================================
    // SMOOTH SCROLL
    // ===================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    const headerHeight = header.offsetHeight;
                    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight;
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // ===================================
    // BACK TO TOP BUTTON
    // ===================================
    const backToTop = document.getElementById('backToTop');
    
    if (backToTop) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });

        backToTop.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // ===================================
    // ANIMATE ON SCROLL (Simple Implementation)
    // ===================================
    const animatedElements = document.querySelectorAll('[data-aos]');
    
    function checkAnimation() {
        animatedElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            const delay = element.getAttribute('data-aos-delay') || 0;
            
            if (elementTop < windowHeight - 100) {
                setTimeout(() => {
                    element.classList.add('aos-animate');
                }, parseInt(delay));
            }
        });
    }

    window.addEventListener('scroll', checkAnimation);
    window.addEventListener('load', checkAnimation);
    checkAnimation(); // Check on init

    // ===================================
    // COUNTER ANIMATION
    // ===================================
    const counters = document.querySelectorAll('[data-count]');
    let countersAnimated = false;

    function animateCounters() {
        if (countersAnimated) return;

        counters.forEach(counter => {
            const rect = counter.getBoundingClientRect();
            if (rect.top < window.innerHeight && rect.bottom > 0) {
                countersAnimated = true;
                const target = parseInt(counter.getAttribute('data-count'));
                const duration = 2000;
                const step = target / (duration / 16);
                let current = 0;

                const updateCounter = () => {
                    current += step;
                    if (current < target) {
                        counter.textContent = Math.floor(current);
                        requestAnimationFrame(updateCounter);
                    } else {
                        counter.textContent = target;
                    }
                };

                updateCounter();
            }
        });
    }

    window.addEventListener('scroll', animateCounters);
    animateCounters();

    // ===================================
    // GALLERY LIGHTBOX
    // ===================================
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    if (galleryItems.length > 0) {
        // Create lightbox element
        const lightbox = document.createElement('div');
        lightbox.className = 'lightbox';
        lightbox.innerHTML = `
            <span class="lightbox__close"><i class="fas fa-times"></i></span>
            <span class="lightbox__nav lightbox__prev"><i class="fas fa-chevron-left"></i></span>
            <span class="lightbox__nav lightbox__next"><i class="fas fa-chevron-right"></i></span>
            <div class="lightbox__content">
                <img src="" alt="">
            </div>
        `;
        document.body.appendChild(lightbox);

        const lightboxImg = lightbox.querySelector('img');
        const lightboxClose = lightbox.querySelector('.lightbox__close');
        const lightboxPrev = lightbox.querySelector('.lightbox__prev');
        const lightboxNext = lightbox.querySelector('.lightbox__next');
        let currentIndex = 0;

        function openLightbox(index) {
            currentIndex = index;
            const img = galleryItems[currentIndex].querySelector('img');
            lightboxImg.src = img.src;
            lightbox.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeLightbox() {
            lightbox.classList.remove('active');
            document.body.style.overflow = '';
        }

        function nextImage() {
            currentIndex = (currentIndex + 1) % galleryItems.length;
            const img = galleryItems[currentIndex].querySelector('img');
            lightboxImg.src = img.src;
        }

        function prevImage() {
            currentIndex = (currentIndex - 1 + galleryItems.length) % galleryItems.length;
            const img = galleryItems[currentIndex].querySelector('img');
            lightboxImg.src = img.src;
        }

        galleryItems.forEach((item, index) => {
            item.addEventListener('click', () => openLightbox(index));
        });

        lightboxClose.addEventListener('click', closeLightbox);
        lightboxNext.addEventListener('click', nextImage);
        lightboxPrev.addEventListener('click', prevImage);

        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox) closeLightbox();
        });

        document.addEventListener('keydown', (e) => {
            if (!lightbox.classList.contains('active')) return;
            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowRight') nextImage();
            if (e.key === 'ArrowLeft') prevImage();
        });
    }

    // ===================================
    // GALLERY FILTERS
    // ===================================
    const filterBtns = document.querySelectorAll('.filter-btn');
    const galleryGrid = document.querySelector('.gallery__grid');
    
    if (filterBtns.length > 0 && galleryGrid) {
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active state
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Filter items
                const filter = btn.getAttribute('data-filter');
                const items = galleryGrid.querySelectorAll('.gallery-item');

                items.forEach(item => {
                    if (filter === 'all' || item.getAttribute('data-category') === filter) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        });
    }

    // ===================================
    // FORM VALIDATION
    // ===================================
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });

            // Email validation
            const emailField = form.querySelector('input[type="email"]');
            if (emailField && emailField.value) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(emailField.value)) {
                    isValid = false;
                    emailField.classList.add('error');
                }
            }

            if (!isValid) {
                e.preventDefault();
            }
        });
    });

    // ===================================
    // ACTIVE NAV LINK
    // ===================================
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinksAll = document.querySelectorAll('.nav__link');
    
    navLinksAll.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPage) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // ===================================
    // PARALLAX EFFECT (Optional)
    // ===================================
    const heroSection = document.querySelector('.hero');
    
    if (heroSection) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const heroContent = heroSection.querySelector('.hero__content');
            if (heroContent && scrolled < window.innerHeight) {
                heroContent.style.transform = `translateY(${scrolled * 0.3}px)`;
                heroContent.style.opacity = 1 - (scrolled / window.innerHeight);
            }
        });
    }

    // ===================================
    // LAZY LOADING IMAGES
    // ===================================
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });

        lazyImages.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for older browsers
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
        });
    }

    // ===================================
    // SCHEDULE TABLE SORTING
    // ===================================
    const scheduleTable = document.querySelector('.schedule-table');
    
    if (scheduleTable) {
        const headers = scheduleTable.querySelectorAll('th');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                const tbody = scheduleTable.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                const isAscending = header.classList.contains('sort-asc');
                
                rows.sort((a, b) => {
                    const aVal = a.cells[index].textContent.trim();
                    const bVal = b.cells[index].textContent.trim();
                    return isAscending ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
                });

                headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
                header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');

                rows.forEach(row => tbody.appendChild(row));
            });
        });
    }

    // ===================================
    // IMAGE OPTIMIZATION - LAZY LOADING
    // ===================================
    // Add lazy loading to all images
    document.querySelectorAll('img:not([loading])').forEach(img => {
        img.loading = 'lazy';
        img.decoding = 'async';
    });
    
    // Handle image loading errors
    document.querySelectorAll('img').forEach(img => {
        img.addEventListener('error', function() {
            this.style.opacity = '0.5';
            this.style.backgroundColor = '#f1f5f9';
        });
    });

    console.log('Lancers Baseball Club - Website initialized successfully! ⚾');
});
