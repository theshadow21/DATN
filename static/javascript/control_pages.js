const linkVideo = "/display_video?video_name="
// const linkVideo = "/stream_video_1?video_name="
const linkStream = "http://localhost:8000"

window.onload = function loadData() {
    console.log("[loadData]");
    callStopStream();
    loadListVideo();
}

function loadListVideo(){
    const url = "/listVideo";
    fetch(url).then((response) => {
        response.json().then((data) => {
            if (data.error) {
                console.log("Data error: ", data.error);
            } else {
                createListVideo(data);
            }
        })
    })
}

function callStopStream(){
    const url = "/stopStreaming";
    fetch(url).then((response) => {
        response.json().then((data) => {
            if (data.error) {
                console.log("Data error: ", data.error);
            } else {
                console.log(data);
            }
        })
    })
}

function createListVideo(data) {
    console.log("[createListVideo]");
    const listVideo = document.getElementById("list-video");
    data.data.forEach(element => {
        console.log("Element: ", element);
        let div = createTagVideo(element);
        listVideo.appendChild(div);
    });
}

function createTagVideo(data){
    let playVideo = document.getElementById("video-display");
    const videoLabel = document.getElementById("video_label");
    let li = document.createElement("h3");
    li.innerHTML=data;
    li.id="li-data";
    li.classList = "text-blue-500 hover:text-red-500 text-sm pt-[20px] pl-[10px]"
    li.onclick = function() {
        playVideo.src = linkVideo + data;
        videoLabel.innerHTML=data
    }
    return li;
}





