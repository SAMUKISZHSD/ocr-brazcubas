document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll para links internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Efeito de scroll na navbar
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 50) {
            navbar.style.backgroundColor = 'rgba(44, 62, 80, 0.98)';
        } else {
            navbar.style.backgroundColor = 'rgba(44, 62, 80, 0.95)';
        }
    });

    // Destacar link ativo na navegação
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section[id]');
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionHeight = section.offsetHeight;
            const scroll = window.scrollY;
            const navLinks = document.querySelectorAll('.nav-link');

            if (scroll >= sectionTop && scroll < sectionTop + sectionHeight) {
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (section.getAttribute('id') === link.getAttribute('href').substring(1)) {
                        link.classList.add('active');
                    }
                });
            }
        });
    });

    // Autoplay do vídeo
    const video = document.querySelector('video');
    if (video) {
        video.play().catch(function(error) {
            console.log("Erro ao reproduzir vídeo:", error);
        });
    }

    // Funções para controlar o skeleton screen
    function showSkeleton(elementId) {
        document.getElementById(elementId).classList.add('active');
    }

    function hideSkeleton(elementId) {
        document.getElementById(elementId).classList.remove('active');
    }

    // Simular carregamento da página
    function simulatePageLoad() {
        // Mostrar todos os skeletons
        showSkeleton('heroSkeleton');
        showSkeleton('feature1Skeleton');
        showSkeleton('feature2Skeleton');
        showSkeleton('feature3Skeleton');
        showSkeleton('step1Skeleton');
        showSkeleton('step2Skeleton');
        showSkeleton('step3Skeleton');
        showSkeleton('step4Skeleton');

        // Esconder os skeletons após um tempo
        setTimeout(() => {
            hideSkeleton('heroSkeleton');
            hideSkeleton('feature1Skeleton');
            hideSkeleton('feature2Skeleton');
            hideSkeleton('feature3Skeleton');
            hideSkeleton('step1Skeleton');
            hideSkeleton('step2Skeleton');
            hideSkeleton('step3Skeleton');
            hideSkeleton('step4Skeleton');
        }, 1500); // 1.5 segundos de delay
    }

    // Iniciar a simulação de carregamento
    simulatePageLoad();

    // Animação dos cards ao entrar na viewport
    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    document.querySelectorAll('.feature-card, .use-case-card, .stat-item').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.5s ease-out';
        observer.observe(card);
    });
}); 