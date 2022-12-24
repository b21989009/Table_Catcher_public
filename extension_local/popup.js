
$(function(){

	// unused button
	/*
	$('#myButton').click(function(){

		(async () => {
			const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
			let result;
			try {
			  [{result}] = await chrome.scripting.executeScript({
				target: {tabId: tab.id},
				func: () => document.body.innerHTML,
			  });
			} catch (e) {
			  document.body.textContent = 'Cannot access page';
			  return;
			}

			console.log(result.slice(0,100) + "..."); // only show a snippet for now
			
		  })();
		
		///const res=await fetch ("https://api.coronavirus.data.gov.uk/v1/data");
		///const record=await res.json();
	
		var server_host = 'http://127.0.0.1:8000/';
		
		fetch(server_host)
		.then(response => response.json())
		//.then(response => sendResponse({farewell: response}))   // ReferenceError: sendResponse is not defined
		.catch(error => console.log(error))


		//chrome.runtime.onMessage.addListener(
		//function(request, sender, sendResponse) {
		//		var url = server_host +  '/get/' ;
		//		return true;  // Will respond asynchronously.
		//});
		
	});
	*/


	$('#scan_button_').click(function(){
		document.getElementById('download_links_table').innerHTML = "";

		//console.log(document.getElementsByTagName('html')[0].innerHTML);
		// this document is the extension pop-up itself. the console is extension's console.

		chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
			let activeTab = tabs[0]; /*** This object does not have like "document" or "html" info in it. */

			chrome.scripting.executeScript(
				{
				target: {tabId: activeTab.id},

				// "function" works as if it is in content_script.js. "document" refers to the active tab page.
				function: function(){return document.getElementsByTagName('html')[0].innerHTML;}
				},
				(res) => {

					// send POST request to backend
					let data_to_send = JSON.stringify({ 'page_url': activeTab.url, 'page_html': res[0].result, 'tag': 'whatever'});
					let posting = $.ajax({
						type: "POST",
						url: "http://127.0.0.1:8000/scan_tables/",
						data: data_to_send,
						processData: false,
						datatype: "jsonp",
						contentType: 'application/json; charset=utf-8',
						beforeSend: function(){console.log("sending"); return"sending";},
						success: function(json_response_from_backend){
							console.log("success");
							createTable_for_DownloadLinks(json_response_from_backend.download_links);
							embed_downloadLinks_on_tables_on_page(json_response_from_backend)
							return "success";
						},
						error: function(){console.log("error"); toastr.error("Failed connect to Server or Not Responding."); return"error";},
					});

				}
			);


			function embed_downloadLinks_on_tables_on_page(downloadLinks_and_tableIndices){
				chrome.tabs.sendMessage(activeTab.id, {data: downloadLinks_and_tableIndices}, function(response) {
						console.log('* * *   sent data to content_script.js   * * * ');
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

});

