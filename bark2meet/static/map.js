let map;
let all_markers = [];
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
    zoom: 15,
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

        //infoWindow.setPosition(pos);
        //infoWindow.setContent("Location found.");
        //infoWindow.open(map);
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
  initializeMarkers();
}


function UpdateUserLocation(url) {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition((position) => {
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

function attachInfoWindow(marker, userToPush){
  console.log(userToPush.full_name);
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
    infoWindow.setContent(infoWindow.content);
    infoWindow.open(map, marker);
    map.setZoom(18);
    map.setCenter(marker.getPosition());
  });
}

function addMarkers(all_locations) {
  for (let i = 0; i < all_locations.length; i++) {
    // for debugging:
    if (all_locations[i].full_name == "Ofir Israeli"){
      all_locations[i].pos_x += 0.0015;
    }
    // end for debb

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
    case 2:
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

  return R * c; //return the distance in metres
}


function createPopupMarker(userInfo) {
  if (userInfo.privacy === "green") {
    return (
      '<div id="infoContentGreen">' +
      '<div class="container1">' +
      '<h1 class="popup-header">New friends for ' +
      userInfo.dog_name +
      "  & You,</h1>" +
      '<h1 class="popup-header">check them out!</h1>' +
      "<div>" +
      '<img src="' +
      removeBaseAddress(userInfo.dog_image) +
      '">' +
      "</div>" +
      '<h2 class="popup-header2Name">' +
      getFirstName(userInfo.full_name) +
      " & " +
      userInfo.dog_name +
      "</h2>" +
      '<h2 class="popup-header2">Only ' +
      distance(userInfo.pos_x, userInfo.pos_y) +
      " away!</h2>" +
      '<div class="infoBox">' +
      '<div class="popup-owner-side">' +
      "<p>" +
      mapGender(userInfo.gender) +
      "</p>" +
      "<p>" +
      mapGender(userInfo.gender) +
      " years old</p>" +
      "</div>" +
      '<div class="vl"></div>' +
      '<div class="popup-dog-side">' +
      "<p>" +
      mapGender(userInfo.dog_gender) +
      "</p>" +
      "<p>" +
      userInfo.dog_age +
      " years old</p>" +
      "</div>" +
      "</div>" +
      '<a href="/profile/'+ userInfo.id +'" class="a">See full profile  <img src="static/arrowside.png"></a>' +
      '<div class="iconsBox">' +
      '<input type="checkbox" onClick="addFriend(this)" name="addFriendBtn" value="'+ userInfo.id +'" class="">' +
      '<i><img id="addFriend" src="static/addfriendgreen.png"  id="bababa"></i>' +
      '<i><img onClick="navigateTo(' + userInfo.pos_x + ', '+ userInfo.pos_y + ')" src="static/navigategreen.png"></i>' +
      '<i><img src="static/pokegreen.png"></i>' +
      "</div>" +
      "</div>" +
      "</div>"
    );
  }
// onClick="addFriend(this)"
  if (userInfo.privacy === "orange") {
    return (
      '<div id="infoContentOrange">' +
      '<div class="container2">' +
      '<h1 class="popup-header">Your friends are out!</h1>' +
      '<h1 class="popup-header">Join their walk</h1>' +
      "<div>" +
      '<img src="static/lisa_dog.svg">' +
      "</div>" +
      '<h2 class="popup-header2Name">' +
      userInfo.full_name +
      " & " +
      userInfo.dog_name +
      "</h2>" +
      '<h2 class="popup-header2">Only ' +
      distance(userInfo.pos_x, userInfo.pos_y) +
      "  away!</h2>" +
      '<a href="/profile/'+ userInfo.id +'" class="a">See full profile  <img src="static/arrowside.png"></a>' +
      '<div class="iconsBox">' +
      '<i><img onClick="navigateTo(' + userInfo.pos_x + ', '+ userInfo.pos_y + ')" src="static/navigateorange.png"></i>' +
      '<i><img src="static/pokeorange.png"></i>' +
      "</div>" +
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


let shouldUpdateLocation = true;
const interval = setInterval(function () {
  if (shouldUpdateLocation) {
    UpdateUserLocation("/update_user_location");
    updateMarkers();
  }
}, 5000);


function openChatWithTarget(userName) {
  let chatDiv = document.getElementById("chat");
  let chatHeader = document.getElementById("chatHeader");
  chatHeader.innerHTML = "Chat With " + userName;
  console.log("Chatting with: " + userName);

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
  if (btn.checked) {
        sendInfo("/add_friend", btn.value);
  }
  else {
        sendInfo("/remove_friend", btn.value);
  }
}

function navigateTo(pos_x, pos_y){
  //todo: make work
  console.log(pos_x);
  console.log(pos_y);
  const req = {
    origin: {lat: pos_x - 0.01, lng: pos_y},
    destination: {lat: pos_x, lng: pos_y},
    provideRouteAlternatives: false,
    travelMode: 'WALKING',
    unitSystem: google.maps.UnitSystem.METRIC
  }

  directionsService.route(req,
    (response, status) => {
      if (status === "OK") {
        directionsRenderer.setDirections(response);
      } else {
        window.alert("Directions request failed due to " + status);
      }
    })
}

function sendInfo(url, value) {
      const URL = url;
      const xhr = new XMLHttpRequest();
      let sender = JSON.stringify(value);
      xhr.open("POST", URL);
      xhr.send(sender);
}





