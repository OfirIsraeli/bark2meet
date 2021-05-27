const ICON = "http://127.0.0.1:5000/static/logo-medium.png";

const askForPermission = () => {
  Notification.requestPermission().then((permission) => {});
};

const showNotification = (title, msg) => {
  const notification = new Notification(title, { body: msg, icon: ICON });
};

const createNotification = (body = "", msg = "") => {
  switch (Notification.permission) {
    case "granted":
      showNotification(body, msg);
    case "default":
      askForPermission();
    case "denied":
      return;
  }
};

$(document).ready(function () {
  var private_socket = io("/private");

  $("#create-notification").on("click", function () {
    createNotification("title", "body");
  });

  $("#new-walk").on("click", function () {
    private_socket.emit("friend-walk");
  });
});
