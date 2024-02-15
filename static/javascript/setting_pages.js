const pic_num = 0;

window.onload = function loadData() {
    console.log("[loadData]");
    getListVideo(true);
    getFreeSpace();
    callStopStream();
}

function getFreeSpace(){
    const url = "/getFreeDisk";
    fetch(url).then((response) => {
        response.json().then((data) => {
            if(data.error){
                console.log("Data error")
            } else {
                updateDiskFree(data);
            }
        })
    })
}

function updateDiskFree(data){
    console.log("Update disk free");
    let progress = document.getElementById("free_space");
    let disk_space = document.getElementById("text_space");
    let total = data.data.total_space_gb.toFixed(2);
    let used = data.data.used_space_gb.toFixed(2);
    let percent = (used/total)*100;
    progress.style.width = percent+"%";
    disk_space.innerHTML = "Total: "+total+"GB, Used: "+used+ "GB";

}

function callStopStream(){
    const url = "/stopStreaming";
    let _video_display = document.getElementById('video_display');
    _video_display.src=""
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

function getListVideo(firstCall){
    const url = "/listVideo";
    fetch(url).then((response) => {
        response.json().then((data) => {
            if (data.error) {
                console.log("Data error: ", data.error);
            } else {
                createListVideo(data, firstCall);
            }
        })
    })
}

function createListVideo(data, firstCall) {
    console.log("[createListVideo]");
    const listVideo = document.getElementById("list-video");
    if(!firstCall){
        while (listVideo.firstChild) {
            listVideo.removeChild(listVideo.lastChild);
        }
    }
    data.data.forEach(element => {
        console.log("Element: ", element);
        let div = createTagVideo(element);
        listVideo.appendChild(div);
    });
}

function createTagVideo(data){
    let playVideo = document.getElementById("video-display");
    const videoLabel = document.getElementById("video_label");
    let new_div = document.createElement("div");
    let span = document.createElement("span");
    let icon = document.createElement("i");
    let li = document.createElement("h3");

    new_div.classList="flex"

    li.innerHTML=data;
    li.id="li-data";
    li.classList = "text-blue-500 text-sm pt-[20px] pl-[10px]"
    li.onclick = function() {

    }
    icon.classList="fa-solid fa-trash pl-[15px] w-[20px] h-[20px] pt-[22px]"
    icon.onclick = function(){
        deleteVideo(data);
    } 
    // span.appendChild(icon)
    new_div.appendChild(li)
    new_div.appendChild(icon)
    return new_div;
}

function deleteVideo(data){
    console.log("deleteVideo: ", data);
    let url = "/deleteVideo?video_name="+data;
    fetch(url).then((response) => {
        response.json().then((data) => {
            if (data.error) {
                console.log("Data error: ", data.error);
            } else {
                console.log(data);
                getListVideo(false);
            }
        })
    })
}

function settingTime(){
    let startTime = document.getElementById('start_time');
    let stopTime = document.getElementById('stop_time');
    if(startTime.value ==="" || stopTime.value ===""){
        alert("Please select time to start and time to stop");
    } else {
        let url = "/settingTimes?startTime="+startTime.value+"&stopTime="+stopTime.value;
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
}

function takePicture (){
    let _takePicture = document.getElementById('take_picture');
    let _video_display = document.getElementById('video_display');
    _takePicture.innerHTML = 'Take Picture';
    _video_display.src = "./video_feed";
    let url = "/takePicture";
    fetch(url).then((response) => {
        response.json().then((data) => {
            if (data.error) {
                console.log("Data error: ", data.error);
                _takePicture.innerHTML = 'Take Picture (Error)';
            } else {
                console.log(data);
                _takePicture.innerHTML = 'Take Picture (OK)';
            }
        })
    })
}



function settingOwner() {
    let _name = document.getElementById('i_name');
    let _email = document.getElementById('i_email');
    if((_name.value ==="")||(_email.value ==="")){
        alert("Please enter a valid email address and name.");
    } else {

        let url = "/settingOwner?name="+_name.value+"&email="+_email.value;
        fetch(url,{
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        }).then((response) => {
            response.json().then((data) => {
                if (data.error) {
                    console.log("Data error: ", data.error);
                } else {
                    console.log(data);
                }
            })
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}

function trainModel() {
    let _train_model = document.getElementById('train_model');
    let _takePicture = document.getElementById('take_picture');
    _takePicture.innerHTML = 'Take picture';
    _train_model.innerHTML = "Waiting...";
    callStopStream();
    let url = "/trainModel";
    fetch(url).then((response) => {
        response.json().then((data) => {
            if (data.error) {
                console.log("Data error: ", data.error);
                _train_model.innerHTML = "Error train"
            } else {
                console.log(data);
                _train_model.innerHTML = "Train model"
            }
        })
    })
}