$(function () {

    // init feather icons
    feather.replace();

    // init tooltip & popovers
    $('[data-toggle="tooltip"]').tooltip();
    $('[data-toggle="popover"]').popover();

    //page scroll
    $('a.page-scroll').bind('click', function (event) {
        var $anchor = $(this);
        $('html, body').stop().animate({
            scrollTop: $($anchor.attr('href')).offset().top
        }, 1000);
        event.preventDefault();
    });

    //toggle scroll menu
    $(window).scroll(function () {
        var scroll = $(window).scrollTop();
        //adjust menu background
        if (scroll >= 100) {
            $('.sticky-navigation').addClass('shadow-bottom');
        } else {
            $('.sticky-navigation').removeClass('shadow-bottom');
        }

        // adjust scroll to top
        if (scroll >= 600) {
            $('.scroll-top').addClass('active');
        } else {
            $('.scroll-top').removeClass('active');
        }
        return false;
    });

    // scroll top top
    $('.scroll-top').click(function () {
        $('html, body').stop().animate({
            scrollTop: 0
        }, 1000);
    });

    //odemter init for videos
    var current = 785541987;
    var el = document.querySelector('.odometer-video');
    odo = new Odometer({
        el: el,
        value: current,
        format: '(,ddd)'
    });
    setInterval(function () {
        var newEmailCount = current + getRandomInt(10, 18); // add average of 14 pr 2 seconds
        odo.update(newEmailCount);
        current = newEmailCount;
    }, 2000);

    /**Theme switcher - DEMO PURPOSE ONLY */
    $('.switcher-trigger').click(function () {
        $('.switcher-wrap').toggleClass('active');
    });
    $('.color-switcher ul li').click(function () {
        var color = $(this).attr('data-color');
        $('#theme-color').attr("href", "css/" + color + ".css");
        $('.color-switcher ul li').removeClass('active');
        $(this).addClass('active');
    });
});

//odemeter random count for videos
function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min)) + min;
}