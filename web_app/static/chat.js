const space = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";

$(document).ready(function () {
  var socket = io.connect("/");

  var socket_messages = io("/messages");

  socket_messages.on("from flask", function (msg) {
    alert(msg);
  });

  socket.on("server orginated", function (msg) {
    alert(msg);
  });

  var private_socket = io("/private");
  private_socket.emit("username");

  $('[id^="chat_with_"]').on("click", function () {
    var recipient = $(this).text().slice(10);
    $(this).next().show();
    fetch("/api/history/" + recipient)
      .then(function (response) {
        return response.json();
      })
      .then(function (text) {
        let history = text.chat;
        history.forEach((entry) => {
          if (entry.sender === recipient) {
            $("#" + recipient).append(
              "<li>" +
                entry.sender +
                ":\t" +
                entry.msg +
                space.repeat(10) +
                entry.send_time +
                "</li>"
            );
          } else {
            $("#" + recipient).append(
              "<li>" + "Me:\t" + entry.msg + space.repeat(10) + entry.send_time + "</li>"
            );
          }
        });
      });
  });

  $('[id^="button_"]').on("click", function () {
    var recipient = $(this).text().slice(8);
    var message_to_send = $("#input_text_" + recipient).val();
    private_socket.emit("private_message", { username: recipient, message: message_to_send });
    $("#input_text_" + recipient).val("");
    $("#" + recipient).append(
      "<li>" + "Me" + ":\t" + message_to_send + space.repeat(10) + new Date() + "</li>"
    );
  });

  private_socket.on("new_private_message", function (data) {
    $("#" + data.username).append(
      "<li>" + data.username + ":\t" + data.msg + space.repeat(10) + data.send_time + "</li>"
    );
  });
  /*
  private_socket.on("new_private_history", function (data) {
    history = data["history"];
    console.log("hi", data["history"], history);
    history.forEach((entry) => {
      $("#" + data.username).append("<li>" + entry.sender + ":\t" + entry.msg + "</li>");
    });
  });*/

  private_socket.on("invalid_user", function (msg) {
    alert(msg);
  });
});

/*
function getHistoryFileName(sender, recipient) {
  HOME_DIR = "chatHistory/";
  if (sender < recipient) {
    return HOME_DIR + sender + "&" + recipient + ".txt";
  }
  return HOME_DIR + recipient + "&" + sender + ".txt";
}

function writeMessageInHistory(sender, recipient, msg) {
  $.get(getHistoryFileName(sender, recipient))
    .done(function () {
      console.log("found");
    })
    .fail(function () {
      console.log("NOT found");
    });
}*/
