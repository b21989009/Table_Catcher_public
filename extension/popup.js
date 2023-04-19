// This document is the extension pop-up itself. The console is extension's console.
// The Popup is reloaded everytime you open it.
// Popup code cannot work after popup is closed. But before that, you can send messages to other scripts to perform functions.

let server_host = "";

$(function(){   // makes sure to start executing after popup's DOM is fully loaded.

	// Check if local server (localhost) is available; else, we will use Azure.
	let checking_local_connection = $.ajax({
		type: "GET",
		url: "http://127.0.0.1:8000/test_connection/",
		success: function(json_response_from_backend){
			console.log("connected to localhost server");
			server_host = "http://127.0.0.1:8000/";
		},
		error: function(){
			console.log("not connected to localhost server")
			server_host = "https://tablecatcher.azurewebsites.net/";
		},
	});


	$('#scan_button_').click(function(){
		document.getElementById('download_links_table').innerHTML = "";

		chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {

			chrome.scripting.executeScript(
				{
				target: {tabId: tabs[0].id},

				// "function" works as if it is in content_script.js. "document" refers to the active tab page.
				function: function(){return document.getElementsByTagName('html')[0].innerHTML;}
				},
				(res) => {

					// send POST request to backend
					let data_to_send = JSON.stringify({ 'page_url': tabs[0].url, 'page_html': res[0].result, 'tag': 'whatever'});
					let send_url = server_host + "scan_tables/";
					let posting = $.ajax({
						type: "POST",
						url: send_url,
						data: data_to_send,
						processData: false,
						datatype: "jsonp",
						contentType: 'application/json; charset=utf-8',
						beforeSend: function(){console.log("sending"); return"sending";},
						success: function(json_response_from_backend){
							console.log("success");
							createTable_for_DownloadLinks(json_response_from_backend.download_links);
							embed_downloadLinks_on_tables_on_page(json_response_from_backend);
							return "success";
						},
						error: function(){console.log("error"); toastr.error("Failed connect to Server or Not Responding."); return"error";},
					});

				}
			);


			function embed_downloadLinks_on_tables_on_page(downloadLinks_and_tableIndices){
				chrome.tabs.sendMessage(tabs[0].id, {data: downloadLinks_and_tableIndices, message:"sending_links"}, function(response) {
						console.log(' sent data to content_script.js ');
				});
			}

			function createTable_for_DownloadLinks(downloadLinks){
				console.log(downloadLinks);

				let table = document.createElement('table');
				let header = document.createElement('thead');
				let tr_ = document.createElement('tr');
				let th_ = document.createElement('th');
				th_.textContent = "Table Links";
				tr_.appendChild(th_);
				header.appendChild(tr_);
				table.appendChild(header);
				let tbody_ = document.createElement('tbody');

				if (downloadLinks.length > 0){

					let show_total = document.createElement('td');
					show_total.textContent = " " + downloadLinks.length + " Tables Found.";
					tbody_.appendChild(show_total);

					/*
					// These links are already on the page now.
					for (let i = 0; i < downloadLinks.length; i++) {
						let row = document.createElement('tr');
						let cell = document.createElement('td');

						let a = document.createElement('a');
						let linkText = document.createTextNode("Table: " + (i+1) );
						a.appendChild(linkText);
						a.href = downloadLinks[i];
						let download_button = document.createElement('i');
						download_button.className = "fa fa-download download_button"
						a.appendChild(download_button)

						cell.appendChild(a);
						row.appendChild(cell);
						tbody_.appendChild(row);
					}
					*/
				}

				else{
					let emptiness = document.createElement('td');
					emptiness.textContent = "No Table Found on this website.";
					tbody_.appendChild(emptiness);
				}

				table.appendChild(tbody_);
				document.getElementById('download_links_table').innerHTML = table.innerHTML;
			}


		}); // since this is async, everything that depends on it has to stay inside.


	});



	$('#screenshot_button_').click(function(){

		chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {

			chrome.tabs.sendMessage(tabs[0].id, {message: "take_screenshot", host_domain: server_host}, function(response) {
				console.log('sent command to content_script.js');

				chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
					if (request.message_me === true) {
						console.log(request.message_);
					}
				});
			});

		});


	});

});


/* JUST FOR TESTING SOME STUFF.

document.addEventListener('DOMContentLoaded', () => {

    // for resetting some stuff when it will be closed. Controlled by background script.
    // chrome.runtime.connect({ name: "popup_opened" });

    const startButton = document.getElementById('captureButton');
    startButton.addEventListener('click', () => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, { command: 'startHighlighting' });
        });
    });

    // DOES NOT WORK.
    intention was: Prevent the shift of focus from the popup to the page (when clicked on page.) Thus prevent the popup from closing.
    setTimeout(function() {
        document.body.focus();
    }, 0);

});

 */