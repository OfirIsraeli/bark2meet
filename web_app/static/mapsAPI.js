let map;
function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: -34.397, lng: 150.644 },
    zoom: 8,
  });
  infoWindow = new google.maps.InfoWindow();
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        var pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };

        const URL = "/home";
        const xhr = new XMLHttpRequest();
        let sender = JSON.stringify([position.coords.latitude, position.coords.longitude]);
        xhr.open("POST", URL);
        xhr.send(sender);

        infoWindow.setPosition(pos);
        infoWindow.setContent("Location found.");
        infoWindow.open(map);
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
      lat: 31.910664,
      lng: 34.896716,
    });
  }

  const image = "static/default-account-img-small.png";
  const marker = new google.maps.Marker({
    position: { lat: 31.7809, lng: 35.2388 },
    map,
    icon: image,
    title: "name",
  });
  marker.addListener("click", () => {
    map.setZoom(12);
    map.setCenter(marker.getPosition());
  });
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
