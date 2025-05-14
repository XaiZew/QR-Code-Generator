function send_to_py() {
    const input = document.getElementById("string").value;

    fetch("http://127.0.0.1:5000/receive", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ data: input })
    })
    .then(response => response.json())
    .then(data => {
        const img = document.getElementById("qr_img");
        img.src = "data:image/png;base64," + data.image;
        img.style.display = "block";
    })
    .catch(error => {
        console.error("Error:", error);
    });
}
