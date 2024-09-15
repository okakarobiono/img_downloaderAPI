document.addEventListener('DOMContentLoaded', () => {
    const mainTitle = document.getElementById('main-title');
    const mainTitleBgColor = document.getElementById('main-title-bg-color');
    const websiteTitle = document.getElementById('website-title');
    const imageContainer = document.getElementById('image-container');
    const image = document.getElementById('image');

    const mainTitleText = document.getElementById('main-title-text');
    const mainTitleColor = document.getElementById('main-title-color');
    const mainTitleSize = document.getElementById('main-title-size');
    const mainTitlePadding = document.getElementById('main-title-padding');
    const mainTitleX = document.getElementById('main-title-x');
    const mainTitleY = document.getElementById('main-title-y');

    const websiteTitleText = document.getElementById('website-title-text');
    const websiteTitleColor = document.getElementById('website-title-color');
    const websiteTitleSize = document.getElementById('website-title-size');
    const websiteTitlePadding = document.getElementById('website-title-padding');
    const websiteTitleX = document.getElementById('website-title-x');
    const websiteTitleY = document.getElementById('website-title-y');

    const saveConfigButton = document.getElementById('save-config');

    const originalWidth = 1200;
    const originalHeight = 760;

    imageContainer.style.width = `${originalWidth}px`;
    imageContainer.style.height = `${originalHeight}px`;
    image.style.width = '100%';
    image.style.height = '100%';

    function updateWatermark(element, text, color, bgColor, size, padding, x, y) {
    element.textContent = text;
    element.style.color = color;
    element.style.backgroundColor = bgColor;
    element.style.fontSize = `${size}px`;
    element.style.padding = `${padding}px`;
    element.style.left = `${x}px`;
    element.style.top = `${y}px`;
    element.style.display = 'block';
}

    function constrainValue(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function addInputListeners(textInput, colorInput, sizeInput, paddingInput, xInput, yInput, element) {
        textInput.addEventListener('input', () => {
            updateWatermark(element, textInput.value, colorInput.value, mainTitleBgColor.value, sizeInput.value, paddingInput.value, xInput.value, yInput.value);
        });
        mainTitleBgColor.addEventListener('input', () => {
            updateWatermark(element, textInput.value, colorInput.value, mainTitleBgColor.value, sizeInput.value, paddingInput.value, xInput.value, yInput.value);
        });
        colorInput.addEventListener('input', () => {
            updateWatermark(element, textInput.value, colorInput.value, mainTitleBgColor.value, sizeInput.value, paddingInput.value, xInput.value, yInput.value);
        });

        sizeInput.addEventListener('input', () => {
            updateWatermark(element, textInput.value, colorInput.value, mainTitleBgColor.value, sizeInput.value, paddingInput.value, xInput.value, yInput.value);
        });

        paddingInput.addEventListener('input', () => {
            updateWatermark(element, textInput.value, colorInput.value, mainTitleBgColor.value, sizeInput.value, paddingInput.value, xInput.value, yInput.value);
        });

        xInput.addEventListener('input', () => {
            xInput.value = constrainValue(xInput.value, 0, originalWidth - element.offsetWidth);
            updateWatermark(element, textInput.value, colorInput.value, mainTitleBgColor.value, sizeInput.value, paddingInput.value, xInput.value, yInput.value);
        });

        yInput.addEventListener('input', () => {
            yInput.value = constrainValue(yInput.value, 0, originalHeight - element.offsetHeight);
           updateWatermark(element, textInput.value, colorInput.value, mainTitleBgColor.value, sizeInput.value, paddingInput.value, xInput.value, yInput.value);
        });
    }

    function makeElementDraggable(element, xInput, yInput) {
        element.addEventListener('mousedown', function(e) {
            let shiftX = e.clientX - element.getBoundingClientRect().left;
            let shiftY = e.clientY - element.getBoundingClientRect().top;

            function moveAt(pageX, pageY) {
                const containerRect = imageContainer.getBoundingClientRect();
                const imageRect = image.getBoundingClientRect();
                const newX = Math.min(Math.max(pageX - shiftX, imageRect.left), imageRect.right - element.offsetWidth);
                const newY = Math.min(Math.max(pageY - shiftY, imageRect.top), imageRect.bottom - element.offsetHeight);

                element.style.left = newX - containerRect.left + 'px';
                element.style.top = newY - containerRect.top + 'px';
                xInput.value = (newX - containerRect.left) * (originalWidth / containerRect.width);
                yInput.value = (newY - containerRect.top) * (originalHeight / containerRect.height);
            }

            function onMouseMove(event) {
                moveAt(event.pageX, event.pageY);
            }

            document.addEventListener('mousemove', onMouseMove);

            document.addEventListener('mouseup', function() {
                document.removeEventListener('mousemove', onMouseMove);
            }, { once: true });

            document.onmouseleave = function() {
                document.removeEventListener('mousemove', onMouseMove);
            };
        });

        element.ondragstart = function() {
            return false;
        };
    }

    addInputListeners(mainTitleText, mainTitleColor, mainTitleSize, mainTitlePadding, mainTitleX, mainTitleY, mainTitle);
    addInputListeners(websiteTitleText, websiteTitleColor, websiteTitleSize, websiteTitlePadding, websiteTitleX, websiteTitleY, websiteTitle);

    makeElementDraggable(mainTitle, mainTitleX, mainTitleY);
    makeElementDraggable(websiteTitle, websiteTitleX, websiteTitleY);

    saveConfigButton.addEventListener('click', () => {
        const config = {
            mainTitle: {
                text: mainTitleText.value,
                color: mainTitleColor.value,
                backgroundColor: mainTitleBgColor.value || '#000000', // Default hitam jika tidak diisi
                size: parseInt(mainTitleSize.value),
                padding: parseInt(mainTitlePadding.value),
                position: {
                left: parseInt(mainTitleX.value),
                top: parseInt(mainTitleY.value)
            }
        },
            websiteTitle: {
                text: websiteTitleText.value,
                color: websiteTitleColor.value,
                size: parseInt(websiteTitleSize.value),
                padding: parseInt(websiteTitlePadding.value),
                position: {
                    left: parseInt(websiteTitleX.value),
                    top: parseInt(websiteTitleY.value)
                }
            }
        };

        fetch('http://127.0.0.1:8000/save-configuration', { // Ensure the correct URL and port
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            alert(data.message);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to save configuration');
        });
    });

    fetch('http://127.0.0.1:8000/load-configuration')
    .then(response => response.json())
    .then(config => {
        if (config.mainTitle) {
            mainTitleText.value = config.mainTitle.text;
            mainTitleColor.value = config.mainTitle.color;
            mainTitleSize.value = config.mainTitle.size;
            mainTitlePadding.value = config.mainTitle.padding;
            mainTitleX.value = config.mainTitle.position.left;
            mainTitleY.value = config.mainTitle.position.top;
            updateWatermark(mainTitle, config.mainTitle.text, config.mainTitle.color, config.mainTitle.backgroundColor, config.mainTitle.size, config.mainTitle.padding, config.mainTitle.position.left, config.mainTitle.position.top);
        }
        if (config.websiteTitle) {
            websiteTitleText.value = config.websiteTitle.text;
            websiteTitleColor.value = config.websiteTitle.color;
            websiteTitleSize.value = config.websiteTitle.size;
            websiteTitlePadding.value = config.websiteTitle.padding;
            websiteTitleX.value = config.websiteTitle.position.left;
            websiteTitleY.value = config.websiteTitle.position.top;
            updateWatermark(websiteTitle, config.websiteTitle.text, config.websiteTitle.color, config.websiteTitle.backgroundColor, config.websiteTitle.size, config.websiteTitle.padding, config.websiteTitle.position.left, config.websiteTitle.position.top);
        }
    })
    .catch(error => {
        console.error('Error loading configuration:', error);
    });
});