let map;
let all_markers = [];
const APP_NAME = "Bark2Meet"

let TIMEOUT = 5000;

let user_pos = {
  lat: 0,
  lng:0,
};

let directionsService;
let directionsRenderer;

function initMap() {
  directionsService = new google.maps.DirectionsService();
  directionsRenderer = new google.maps.DirectionsRenderer();
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 31.771959, lng: 35.217018 },
    zoom: 17,
    mapId:'a856c89da17dedb6',
  });
  directionsRenderer.setMap(map);
  infoWindow = new google.maps.InfoWindow();
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        var pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };

        user_pos= pos;

        UpdateUserLocation("/update_user_location");

        map.setCenter(pos);
      },
      () => {
        handleLocationError(true, infoWindow, map.getCenter());
      }
    );
  } else {
    // Browser doesn't support Geolocation
    handleLocationError(false, infoWindow, map.getCenter());
    map.setCenter({
      lat: 31.771959,
      lng: 35.217018,
    });
  }
  var geoloccontrol = new klokantech.GeolocationControl(map, 1);

  initializeMarkers();
  if(!checkIfFriendsAround()){
    checkIfRushHour()
  }
}


function UpdateUserLocation(url) {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition((position) => {
      var pos = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };

      user_pos= pos;
      const URL = url;
      const xhr = new XMLHttpRequest();
      let sender = JSON.stringify([position.coords.latitude, position.coords.longitude]);
      xhr.open("POST", URL);
      xhr.send(sender);
    });
  }
}


function initializeMarkers() {
  fetch("/api/locations")
    .then(function (response) {
      return response.json();
    })
    .then(function (all_locations) {
      addMarkers(all_locations);
    });
}

function checkIfFriendsAround() {
  let result = false;
  fetch("/api/are_friends_around")
    .then(function (response) {
      return response.json();
    })
    .then(function (friendsAround) {
      if (friendsAround > 0){
        createNotification(APP_NAME, "You have " + friendsAround + " friends walking around. Join them!");
        result = true;

      }
    });
    return result;
}

function checkIfRushHour() {
  fetch("/api/rush_hour_check")
    .then(function (response) {
      return response.json();
    })
    .then(function (walkersAround) {
      if (walkersAround > 0 ){
        createNotification(APP_NAME, "There are " + walkersAround + " walkers around you. Join them!");

      }
    });
}


function attachInfoWindow(marker, userToPush){
  let infoWindow;


  // green\orange person marker options
  if (userToPush.privacy === "green" || userToPush.privacy === "orange") {
    // open infowindow    
    infoWindow = new google.maps.InfoWindow({
      content: createPopupMarker(userToPush),
    });
  }

  // red person marker options
  else if (userToPush.privacy === "red"){
    // open infowindow
    infoWindow = new google.maps.InfoWindow({
      content: createPopupMarker(userToPush),
      maxWidth: 250,
    });
  }

  // me
  else {
    infoWindow = new google.maps.InfoWindow({});
  }
  infoWindow.addListener("closeclick", function () {
    shouldUpdateLocation = true;
  });

  marker.addListener("click", function () {
    // DISABLE LOCATION UPDATE
    if (userToPush.privacy !== "me"){
            shouldUpdateLocation = false;
    }

    /*if (userToPush.status === 0) {
      shouldUpdateLocation = true;
    }*/

    infoWindow.setContent(infoWindow.content);
    infoWindow.open(map, marker);
    map.setZoom(18);
    map.setCenter(marker.getPosition());
  });
}

function addMarkers(all_locations) {
  for (let i = 0; i < all_locations.length; i++) {
    // for debugging:
    if (all_locations[i].full_name === "Shir Mazor"){
      all_locations[i].pos_x += 0.0015;
    }
    if (all_locations[i].full_name === "Ofir Israeli"){
      all_locations[i].pos_x = 32.068348;
      all_locations[i].pos_y = 34.795463;
    }


    // end for debugging

    const marker = new google.maps.Marker({
      position: new google.maps.LatLng(all_locations[i].pos_x, all_locations[i].pos_y),
      icon: all_locations[i].image,
      map: map,
    });
    attachInfoWindow(marker, all_locations[i])
    all_markers.push(marker);
  }
}


function updateMarkers() {
  fetch("/api/locations")
    .then(function (response) {
      return response.json();
    })
    .then(function (all_locations) {
      // remove all users locations
      for (let i = 0; i < all_markers.length; i++) {
        all_markers[i].setMap(null);
      }
      all_markers = [];
      // update all users locations
      addMarkers(all_locations);
    });
}


function mapGender(genderNumber) {
  switch (genderNumber) {
    case 1:
      return "Male";
    case 0:
      return "Female";
    case 3:
      return "Unidentified";
  }
}


function getFirstName(fullName) {
  return fullName.split(/(\s+)/)[0];
}


function removeBaseAddress(address) {
  if (address === "static/default-account-img.png"){
    return address;
  }
  return address.slice(10);
}


function distance(user_lat, user_lng){
  const R = 6371e3; // radius of earth in metres
  const ph1 = user_pos.lat * Math.PI/180; // φ, λ in radians
  const ph2 = user_lat * Math.PI/180;
  const delta_ph = (user_lat-user_pos.lat) * Math.PI/180;
  const delata_gama = (user_lng-user_pos.lng) * Math.PI/180;

  const a = Math.sin(delta_ph/2) * Math.sin(delta_ph/2) +
            Math.cos(ph1) * Math.cos(ph2) *
            Math.sin(delata_gama/2) * Math.sin(delata_gama/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

  return Math.trunc(R * c); //return the distance in metres
}


function newFriendsTeaser(userInfo){
  if (userInfo.is_friend === true){
    return '<h1 class="popup-header">Say Hello to your Friends!' + "</h1>"
  }
  return '<h1 class="popup-header">New friends!</h1>' +
          '<h1 class="popup-header">check them out!</h1>'
}

function addFriendButton(userInfo){
    if (userInfo.is_friend === true){
      return ""
    }
    return '<input type="checkbox" onClick="addFriend(this)" value="'+ userInfo.id +'">' +
    '<div class="icon-box-green">' +
        '<i class="fas fa-user-plus" aria-hidden="true"></i>' +
    '</div>'

}


function createPopupMarker(userInfo) {
  if(userInfo.status === 0 || userInfo.status === -1 ||(userInfo.status === 3 && userInfo.privacy !== "red")){
    return (
    '<div id="infoContentNotWalking">' +
    '<div class="container3">' +
    '<h1 class="popup-header">Privacy Mode</h1>' +
    "<div>" +
    "<p class='popup-dog-side'> Please change privacy mode <br> to see users details </p>" +
    "</div>" +
    "</div>" +
    "</div>"
  );
  }

  if (userInfo.privacy === "green") {
    return (
      '<div id="infoContentGreen">' +
      '<div class="container1">' +
      newFriendsTeaser(userInfo) +
          "<div class='profile-titles'>" +
                '<a href="/profile/'+ userInfo.id +'" class="a">' +
      "<img class='owner-pic' src='"+ removeBaseAddress(userInfo.user_image) +"'>" +
      "<img class='dog-pic' src='" + removeBaseAddress(userInfo.dog_image) + "'>" +
                  "</a>" +
      "<div class='names'>" +
      "<span class='owner-name'>"+ getFirstName(userInfo.full_name) +"</span>" +
      "<span> & </span>" +
      "<span class='dog-name'>" + userInfo.dog_name +"</span>" +
      "</div>" +
        "</div>" +

      '<h2 class="popup-header2">Only ' +
      distance(userInfo.pos_x, userInfo.pos_y) +
      "m away!</h2>" +
      '<div class="infoBox">' +
      '<div class="popup-owner-side">' +
      "<p>" +
      mapGender(userInfo.gender) +
      "</p>" +
      "<p>" +
      userInfo.age +
      " Years Old</p>" +
      "</div>" +
      '<div class="vl"></div>' +
      '<div class="popup-dog-side">' +
      "<p>" +
      mapGender(userInfo.dog_gender) +
      "</p>" +
      "<p>" +
      Math.trunc(userInfo.dog_age) +
      " Years Old</p>" +
      "</div>" +
      "</div>" +

       '<div class="green-btns">' +
                        '<div class="col-xs-4 pull-right">' +
                        checkFriendStatus(userInfo) +
                        '</div>' +
                        '<div class="col-xs-4 pull-right">' +
                          '<input type="checkbox" onClick="navigateTo('  + 'this, ' + userInfo.pos_x + ', '+ userInfo.pos_y + ')">' +
                          '<div class="icon-box-green">' +
                            '<i class="fas fa-location-arrow" aria-hidden="true"></i>' +
                          '</div>' +
                        '</div>' +
        '</div>' +
      "</div>" +
      "</div>"
    );
  }

  if (userInfo.privacy === "orange") {
    return (
      '<div id="infoContentOrange">' +
      '<div class="container2">' +
      '<h1 class="popup-header">Your friends are out!</h1>' +
      '<h1 class="popup-header">Join their walk</h1>' +

          "<div class='profile-titles'>" +
          '<a href="/profile/'+ userInfo.id +'" class="a">' +
      "<img class='owner-pic' src='"+ removeBaseAddress(userInfo.user_image) +"'>" +
      "<img class='dog-pic' src='" + removeBaseAddress(userInfo.dog_image) + "'>" +
                            "</a>" +

      "<div class='names'>" +
      "<span class='owner-name'>"+ getFirstName(userInfo.full_name) +"</span>" +
      "<span> & </span>" +
      "<span class='dog-name'>" + userInfo.dog_name +"</span>" +
      "</div>" +
        "</div>" +

      '<h2 class="popup-header2">Only ' +
      distance(userInfo.pos_x, userInfo.pos_y) +
      "m away!</h2>" +

          '<div class="orange-btns">' +
                                '<div class="col-xs-4 pull-right">' +
                                  '<input type="checkbox" onClick="navigateTo(' + userInfo.pos_x + ', '+ userInfo.pos_y + ')">' +
                                  '<div class="icon-box-orange">' +
                                    '<i class="fas fa-location-arrow" aria-hidden="true"></i>' +
                                  '</div>' +
                                '</div>' +
          '</div>' +

      "</div>" +
      "</div>"
    );
  }

  return (
    '<div id="infoContentRed">' +
    '<div class="container3">' +
    '<h1 class="popup-header">Pay attention:</h1>' +
    '<h1 class="popup-header">A ' +
    userInfo.dog_breed +
    "  is nearby...</h1>" +
    "<div>" +
    "<p class='popup-dog-side'>These two are on private mode. so you can't reach out this time.</p>" +
    "</div>" +
    "</div>" +
    "</div>"
  );
}

function checkFriendStatus(userInfo){
  if (userInfo.is_friend){
    return ('<button id="AreadyFriend">' +
            '<i class="fas fa-user-check" aria-hidden="true"></i>' +
            '</button>')
  }

  if (userInfo.send_friend_req){
    return ('<button id="requestFriend">' +
            '<i class="fas fa-user-clock" aria-hidden="true"></i>' +
            '</button>')
  }

  return ('<input type="checkbox" onClick="addFriend(this)" value="'+ userInfo.id +'">' +
    '<div class="icon-box-green">' +
      '<i class="fas fa-user-plus" aria-hidden="true"></i>' +
    '</div>')
}


let shouldUpdateLocation = true;
const interval = setInterval(function () {
  if (shouldUpdateLocation) {
    UpdateUserLocation("/update_user_location");
    updateMarkers();
  }
}, TIMEOUT);


function openChatWithTarget(userName) {
  let chatDiv = document.getElementById("chat");
  let chatHeader = document.getElementById("chatHeader");
  chatHeader.innerHTML = "Chat With " + userName;

  chatDiv.style.display = "block";
}


function handleLocationError(browserHasGeolocation, infoWindow, pos) {
  infoWindow.setPosition(pos);
  infoWindow.setContent(
    browserHasGeolocation
      ? "Error: The Geolocation service failed."
      : "Error: Your browser doesn't support geolocation."
  );
  infoWindow.open(map);
}

function addFriend(btn){
  $("#realtime_porter").trigger("port_friend_request",[btn.value])
  if (btn.checked) {
        sendInfo("/send_friend_request", btn.value);
  }
  else {
        sendInfo("/unsend_friend_request", btn.value);
  }
}

function update_status(statusCode){
  sendInfo("/api/update_status", statusCode);
}


let onNavigation = false;
function navigateTo(src, dest_x, dest_y){
  if (navigator.geolocation) {
    if (!onNavigation){
      const req = {
        origin: {lat: user_pos.lat, lng: user_pos.lng},
        destination: {lat: dest_x, lng: dest_y},
        provideRouteAlternatives: false,
        travelMode: 'WALKING',
        unitSystem: google.maps.UnitSystem.METRIC
      }
    
      directionsService.route(req,
        (response, status) => {
          if (status === "OK") {            
            directionsRenderer.setDirections(response);
            resetNavigation(dest_x, dest_y)
          } else {
            window.alert("Directions request failed due to " + status);
          }
        })
    }
    else{
      directionsRenderer.setDirections({routes: [], geocoded_waypoints: []});
    }
    onNavigation = !onNavigation;


  }}

let endNavigationInterval;
function resetNavigation(tX, tY){
  endNavigationInterval = setInterval(()=>{

    const curDist = distance(tX, tY)
    if(curDist < 30){
      directionsRenderer.setDirections({routes: [], geocoded_waypoints: []});
      clearInterval(endNavigationInterval);

    }
  }, 1000)
}


function sendInfo(url, value) {
      const URL = url;
      const xhr = new XMLHttpRequest();
      let sender = JSON.stringify(value);
      xhr.open("POST", URL);
      xhr.send(sender);
}


// navigator.serviceWorker.getRegistration("/").then(reg=>{
//   console.log(reg)
//   reg.pushManager.subscribe({
//     userVisibleOnly: true
//   }).then(sub=>{
//     sendInfo("/api/notification_subscribe", sub.toJSON())
//   })
// })



