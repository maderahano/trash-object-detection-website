/*==================== MENU SHOW Y HIDDEN ====================*/
const navMenu = document.getElementById('nav-menu'),
      navToggle = document.getElementById('nav-toggle'),
      navClose = document.getElementById('nav-close')


/*===== MENU SHOW =====*/
/* Validate if constant exists */
if(navToggle){
    navToggle.addEventListener('click', ()=> {
        navMenu.classList.add('show-menu')
    })
}

/*===== MENU HIDDEN =====*/
/* Validate if constant exists */
if(navClose){
    navClose.addEventListener('click', ()=> {
        navMenu.classList.remove('show-menu')
    })
}

/*==================== REMOVE MENU MOBILE ====================*/
const navLink = document.querySelectorAll('.nav__link')

function linkAction(){
    const navMenu = document.getElementById('nav-menu')
    // When we click on each nav__link, we remove the show-menu class
    navMenu.classList.remove('show-menu')
}
navLink.forEach(n => n.addEventListener('click', linkAction))

/*==================== ACCORDION SKILLS ====================*/
const skillsContent = document.getElementsByClassName('skills__content'),
      skillsHeader = document.querySelectorAll('.skills__header')

function toggleSkills(){
    let itemClass = this.parentNode.className

    for(i = 0; i < skillsContent.length; i++){
        skillsContent[i].className = 'skills__content skills__close'
    }
    if(itemClass === 'skills__content skills__close'){
        this.parentNode.className = 'skills__content skills__open'
    }
}

skillsHeader.forEach((el) => {
    el.addEventListener('click', toggleSkills)
})

/*==================== QUALIFICATION TABS ====================*/
const tabs = document.querySelectorAll('[data-target]'),
      tabContents = document.querySelectorAll('[data-content]')

tabs.forEach(tab =>{
    tab.addEventListener('click', () =>{
        const target = document.querySelector(tab.dataset.target)

        tabContents.forEach(tabContent =>{
            tabContent.classList.remove('qualification__active')
        })
        target.classList.add('qualification__active')

        tabs.forEach(tab =>{
            tab.classList.remove('qualification__active')
        })
        tab.classList.add('qualification__active')
    })
})

/*==================== UPLOAD DETECTION ====================*/
// $(document).ready(function() {
//     $('#uploadImage').submit(function(event) {
//         if($('#uploadImageFile').val()) {
//             event.preventDefault();
//             // alert('success');

//             $('#targetLayer').hide();
//             $(this).ajaxSubmit({
//                 target: '#targetLayer',
//                 beforeSubmit: function() {
//                     $('.progress-bar').width('50%');
//                 },
//                 uploadProgress: function(event, position, total, percentageComplete) {
//                     $('.progress-bar').animate({
//                         width: percentageComplete + '%'
//                     }, {
//                         duration: 1000
//                     });
//                 },
//                 success: function(data) {
//                     $('#targetLayer').show();
//                     $('#targetLayer').append(data.htmlresponse);
//                 },
//                 resetForm: true
//             });
//         }
//         return false;
//     });
// });

/*==================== IMAGE DETECTION MODAL ====================*/
const imageDetectionModalViews = document.querySelectorAll('.image-detection__modal'),
      imageDetectionModalBtns = document.querySelectorAll('.image-detection__content')
    
let imageDetectionModal = function(imageDetectionModalClick){
    imageDetectionModalViews[imageDetectionModalClick].classList.add('active-modal-image-detection')
}

imageDetectionModalBtns.forEach((imageDetectionModalBtn, i) => {
    imageDetectionModalBtn.addEventListener('click', () => {
        imageDetectionModal(i)
    })
})

imageDetectionModalViews.forEach((modalCloseEsc) => {
    modalCloseEsc.addEventListener('keydown', (e) => {
        imageDetectionModalViews.forEach((imageDetectionModalView) => {
            if (e.keyCode === 27) {
                imageDetectionModalView.classList.remove('active-modal-image-detection')
            };
        })
    })
})

$(document).ready(function() {
    document.getElementById("uploadImageFile").onchange = function() {
        document.getElementById("uploadImage").submit(function(event) {
            if($('#uploadImageFile').val()) {
                event.preventDefault();
            }
            return false;
        });
        
        imageDetectionModalViews.forEach((imageDetectionModalView) => {
            imageDetectionModalView.classList.remove('active-modal-image-detection')
        })
    }
});

/* Modal Upload Image */
$(document).ready(function (e) {
    $('#image-upload-custom').on('click', function () {
        $('#image-upload-custom').change(function (event) {
            event.preventDefault();
            var formData = new FormData();
            var ins = document.getElementById('image-upload-custom').files.length;
    
            for (var i = 0; i < ins; i++) {
                formData.append("file", document.getElementById('image-upload-custom').files[i]);
            }
    
            $.ajax({
                url: '/detect-image',
                dataType: 'json',
                cache: false,
                contentType: false,
                processData: false,
                data: formData,
                type: 'post',
                success: function (response) {
                    console.log("upload success", response);
                    $('#targetLayer').append(data.htmlresponse);
                },
                error: function (response) {
                    console.log("upload error", response);
                    console.log(response.getAllResponseHeaders());
                }
            });

            imageDetectionModalViews.forEach((imageDetectionModalView) => {
                imageDetectionModalView.classList.remove('active-modal-image-detection')
            })
        });
    });

    $('#image-upload-custom').on('drop', function () {
        $('#image-upload-custom').change(function () {
            var formData = new FormData();
            var ins = document.getElementById('image-upload-custom').files.length;

            for (var i = 0; i < ins; i++) {
                formData.append("file", document.getElementById('image-upload-custom').files[i]);
            }

            $.ajax({
                url: 'detect-image',
                dataType: 'json',
                cache: false,
                contentType: false,
                processData: false,
                data: formData,
                type: 'post',
                success: function (response) {
                    console.log("upload success", response);
                    $('#msg').html('');
                    $.each(response, function(key, data) {
                        if (key !== 'message') {
                            $('#msg').append(key + ' -> ' + data + '<br/>');
                        } else {
                            $('#msg').append(data + '<br/>');
                        }
                    });
                },
                error: function (response) {
                    console.log("upload error", response);
                    console.log(response.getAllResponseHeaders());
                    $('#msg').html(response.message);
                }  
            });

            imageDetectionModalViews.forEach((imageDetectionModalView) => {
                imageDetectionModalView.classList.remove('active-modal-image-detection')
            })
        });
    });
});

/*==================== VIDEO DETECTION MODAL ====================*/
const videoDetectionModalViews = document.querySelectorAll('.video-detection__modal'),
      videoDetectionModalBtns = document.querySelectorAll('.video-detection__content')
    
let videoDetectionModal = function(videoDetectionModalClick){
    videoDetectionModalViews[videoDetectionModalClick].classList.add('active-modal-video-detection')
}

videoDetectionModalBtns.forEach((videoDetectionModalBtn, i) => {
    videoDetectionModalBtn.addEventListener('click', () => {
        videoDetectionModal(i)
    })
})

videoDetectionModalViews.forEach((modalCloseEsc) => {
    modalCloseEsc.addEventListener('keydown', (e) => {
        videoDetectionModalViews.forEach((videoDetectionModalView) => {
            if (e.keyCode === 27) {
                videoDetectionModalView.classList.remove('active-modal-video-detection')
            };
        })
    })
})

$(document).ready(function() {
    document.getElementById("uploadVideoFile").onchange = function() {
        document.getElementById("uploadVideo").submit(function(event) {
            if($('#uploadVideoFile').val()) {
                event.preventDefault();
            }
            return false;
        });
        
        videoDetectionModalViews.forEach((videoDetectionModalView) => {
            videoDetectionModalView.classList.remove('active-modal-video-detection')
        })
    }
});

/* Modal Upload video */
$(document).ready(function (e) {
    $('#video-upload-custom').on('click', function () {
        $('#video-upload-custom').change(function () {
            var formData = new FormData();
            var ins = document.getElementById('video-upload-custom').files.length;
    
            for (var i = 0; i < ins; i++) {
                formData.append("file", document.getElementById('video-upload-custom').files[i]);
            }
    
            $.ajax({
                url: '/detect-video',
                dataType: 'json',
                cache: false,
                contentType: false,
                processData: false,
                data: formData,
                type: 'post',
                success: function (response) {
                    console.log("upload success", response);
                    $('#msg').html('');
                    $.each(response, function(key, data) {
                        if (key !== 'message') {
                            $('#msg').append(key + ' -> ' + data + '<br/>');
                        } else {
                            $('#msg').append(data + '<br/>');
                        }
                    })
                },
                error: function (response) {
                    console.log("upload error", response);
                    console.log(response.getAllResponseHeaders());
                    $('#msg').html(response.message);
                }
            });

            videoDetectionModalViews.forEach((videoDetectionModalView) => {
                videoDetectionModalView.classList.remove('active-modal-video-detection')
            })
        });
    });

    $('#video-upload-custom').on('drop', function () {
        $('#video-upload-custom').change(function () {
            var formData = new FormData();
            var ins = document.getElementById('video-upload-custom').files.length;

            for (var i = 0; i < ins; i++) {
                formData.append("file", document.getElementById('video-upload-custom').files[i]);
            }

            $.ajax({
                url: 'detect-video',
                dataType: 'json',
                cache: false,
                contentType: false,
                processData: false,
                data: formData,
                type: 'post',
                success: function (response) {
                    console.log("upload success", response);
                    $('#msg').html('');
                    $.each(response, function(key, data) {
                        if (key !== 'message') {
                            $('#msg').append(key + ' -> ' + data + '<br/>');
                        } else {
                            $('#msg').append(data + '<br/>');
                        }
                    });
                },
                error: function (response) {
                    console.log("upload error", response);
                    console.log(response.getAllResponseHeaders());
                    $('#msg').html(response.message);
                }  
            });

            videoDetectionModalViews.forEach((videoDetectionModalView) => {
                videoDetectionModalView.classList.remove('active-modal-video-detection')
            })
        });
    });
});

let swiper = new Swiper(".show-image-detection__container", {
    navigation: {
      nextEl: ".swiper-button-next",
      prevEl: ".swiper-button-prev",
    },
  });

let swiperResultImage = new Swiper('.show-image-detection__container', {
    cssMode: true,
    loop: true,
    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
    },
    pagination: {
        el: '.swiper-pagination',
        clickable: true,
    },
});

/*==================== LIVE WEBCAM DETECTION MODAL ====================*/

// var buttonRecord = document.getElementById("record");
// var buttonStop = document.getElementById("stop");

// buttonStop.disabled = true;

// buttonRecord.onclick = function() {
//     buttonRecord.disabled = true;
//     buttonStop.disabled = false;

//     // Disable Download Link
//     var downloadLink = document.getElementById("download");
//     downloadLink.text = "";
//     downloadLink.href = "";

//     // XMLHttpRequest
//     var xhr = new XMLHttpRequest();
//     xhr.onreadystatechange = function() {
//         if (xhr.readyState == 4 && xhr.status == 200) {
//             // alert(xhr.responseText);
//         }
//     }
//     xhr.open("POST", "/record_status");
//     xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
//     xhr.send(JSON.stringify({status: "true"}));
// }

// buttonStop.onclick = fucntion() {
//     buttonRecord.disabled = false;
//     buttonStop.disabled = true;

//     // XMLHttpRequest
//     var xhr = new XMLHttpRequest();
//     xhr.onreadystatechange = function() {
//         if (xhr.readyState == 4 && xhr.status == 200) {
//             // alert(xhr.responseText);

//             // Enable Download Link
//             var downloadLink = document.getElementById("download");
//             downloadLink.text = "Download Video";
//             downloadLink.href = "/static/video.avi";
//         }
//     }
//     xhr.open("POST", "/record_status");
//     xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
//     xhr.send(JSON.stringify({ status: "false" }));
// }

/*==================== LIVE DRONE DETECTION MODAL ====================*/

/* Modal Upload Data Link RTMP */
// $(document).ready(function () {
//     $('form').on('submit', function (event) {
//         $.ajax({
//             url: '/live-drone',
//             type: 'post',
//             data : {
//                 link_rtmp : $('#linkrtmpInput').val()
//             }
//         });
//         console.log(data)
//         event.preventDefault();
//     });
// });

/*==================== DRONE DETECTION MODAL ====================*/
// const droneDetectionModalViews = document.querySelectorAll('.drone-detection__modal'),
//       droneDetectionModalBtns = document.querySelectorAll('.drone-detection__content'),
//       droneDetectionModalCloses = document.querySelectorAll('.drone-detection__modal-close')
    
// let droneDetectionModal = function(droneDetectionModalClick){
//     droneDetectionModalViews[droneDetectionModalClick].classList.add('active-modal-drone-detection')
// }

// droneDetectionModalBtns.forEach((droneDetectionModalBtn, i) => {
//     droneDetectionModalBtn.addEventListener('click', () => {
//         droneDetectionModal(i)
//     })
// })

// droneDetectionModalCloses.forEach((modalClose) => {
//     modalClose.addEventListener('click', () => {
//         droneDetectionModalViews.forEach((droneDetectionModalView) => {
//             droneDetectionModalView.classList.remove('active-modal-drone-detection')
//         })
//     })
// })

// droneDetectionModalViews.forEach((modalCloseEsc) => {
//     modalCloseEsc.addEventListener('keydown', (e) => {
//         droneDetectionModalViews.forEach((droneDetectionModalView) => {
//             if (e.keyCode === 27) {
//                 droneDetectionModalView.classList.remove('active-modal-drone-detection')
//             };
//         })
//     })
// })

/*==================== Stream Drone ====================*/
if (Hls.isSupported()) {
    var video = document.getElementById('streamDrone');
    var hls = new Hls();
    // bind them together
    hls.attachMedia(video);
    hls.on(Hls.Events.MEDIA_ATTACHED, function () {
      console.log("video and hls.js are now bound together !");
      hls.loadSource("http://<ip-address-of-web-server>/live/mystream.m3u8");
      hls.on(Hls.Events.MANIFEST_PARSED, function (event, data) {
        console.log("manifest loaded, found " + data.levels.length + " quality level");
      });
    });
  }

/*==================== PORTFOLIO SWIPER ====================*/
let swiperPortfolio = new Swiper('.portfolio__container', {
    cssMode: true,
    loop: true,
    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
    },
    pagination: {
        el: '.swiper-pagination',
        clickable: true,
    },
});

/*==================== TESTIMONIAL SWIPER ====================*/
let swiperTestimonial = new Swiper('.testimonial__container', {
    loop: true,
    grabCursor: true,
    spaceBetween: 48,

    pagination: {
        el: '.swiper-pagination',
        clickable: true,
        dynamicBullets: true,
    },
    breakpoints: {
        568: {
            slidesPerView: 2,
        },
    },
});

/*==================== SCROLL SECTIONS ACTIVE LINK ====================*/
const sections = document.querySelectorAll('section[id]')

function scrollActive(){
    const scrollY = window.pageYOffset

    sections.forEach(current => {
        const sectionHeight = current.offsetHeight
        const sectionTop = current.offsetTop - 50;
        sectionId = current.getAttribute('id')

        if(scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
            document.querySelector('.nav__menu a[href*=' + sectionId + ']').classList.add('active-link')
        } else {
            document.querySelector('.nav__menu a[href*=' + sectionId + ']').classList.remove('active-link')
        }
    })
}
window.addEventListener('scroll', scrollActive)

/*==================== CHANGE BACKGROUND HEADER ====================*/
function scrollHeader() {
    const nav = document.getElementById('header')

    // When the scroll is greater than 80 viewport height, add the scroll-header class to the header tag
    if(this.scrollY >= 80) nav.classList.add('scroll-header'); else nav.classList.remove('scroll-header')
}
window.addEventListener('scroll', scrollHeader)

/*==================== SHOW SCROLL UP ====================*/
function scrollUp() {
    const scrollUp = document.getElementById('scroll-up')

    //When the scroll is highet than 80 viewport height, add the show-scroll class to the tag scroll-up tag
    if(this.scrollY >= 560) scrollUp.classList.add('show-scroll'); else scrollUp.classList.remove('show-scroll')
}
window.addEventListener('scroll', scrollUp)

/*==================== DARK LIGHT THEME ====================*/
const themeButton = document.getElementById('theme-button')
const darkTheme = 'dark-theme'
const iconTheme = 'uil-sun'

// Previously selected topic (if user selected)
const selectedTheme = localStorage.getItem('selected-theme')
const selectedIcon = localStorage.getItem('selected-icon')

// We obtain the current theme that the interface has by validating the dark-theme class
const getCurrentTheme = () => document.body.classList.contains(darkTheme) ? 'dark' : 'light'
const getCurrentIcon = () => themeButton.classList.contains(iconTheme) ? 'uil-moon' : 'uil-sun'

// We validate if the user previously these a topic
if (selectedTheme) {
    // If the validation is fulfilled, we ask what the issue was to know is we activated or deactivated the dark
    document.body.classList[selectedTheme === 'dark' ? 'add' : 'remove'](darkTheme)
    themeButton.classList[selectedIcon === 'uil-moon' ? 'add' : 'remove'](iconTheme)
}

// Activate / deactivate the theme manually with the button
themeButton.addEventListener('click', () => {
    // Add or remove the dark / icon theme
    document.body.classList.toggle(darkTheme)
    themeButton.classList.toggle(iconTheme)

    // We save the theme and the current icon that user close
    localStorage.setItem('selected-theme', getCurrentTheme())
    localStorage.setItem('selected-item', getCurrentIcon())
})