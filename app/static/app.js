const fileInput = document.getElementById("fileInput");

const uploadCard = document.getElementById("uploadCard");
const loading = document.getElementById("loading");
const resultCard = document.getElementById("resultCard");
const errorBox = document.getElementById("error");

const fileName = document.getElementById("fileName");
const description = document.getElementById("description");

const pages = document.getElementById("pages");
const extractionTime = document.getElementById("extractionTime");
const analysisTime = document.getElementById("analysisTime");

const newButton = document.getElementById("newButton");


fileInput.addEventListener("change", async () => {

    const file = fileInput.files[0];

    if (!file) {
        return;
    }

    fileName.textContent = `Selected: ${file.name}`;

    await analyzePDF(file);
});


async function analyzePDF(file) {

    hideError();

    uploadCard.hidden = true;
    resultCard.hidden = true;
    loading.hidden = false;

    try {

        const formData = new FormData();

        formData.append("file", file);


        const response = await fetch(
            "/upload",
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to analyze PDF."
            );

        }


        // ---------------------------------
        // DISPLAY RESULT
        // ---------------------------------

        description.textContent =
            data.description;

        pages.textContent =
            data.pages;

        extractionTime.textContent =
            `${data.extraction_time_ms} ms`;

        analysisTime.textContent =
            `${(data.analysis_time_ms / 1000).toFixed(2)} s`;


        loading.hidden = true;
        resultCard.hidden = false;

    }

    catch (error) {

        loading.hidden = true;
        uploadCard.hidden = false;

        showError(error.message);

    }

}


newButton.addEventListener("click", () => {

    fileInput.value = "";

    fileName.textContent = "";

    resultCard.hidden = true;

    errorBox.hidden = true;

    uploadCard.hidden = false;

});


function showError(message) {

    errorBox.textContent =
        `⚠️ ${message}`;

    errorBox.hidden = false;

}


function hideError() {

    errorBox.hidden = true;

}