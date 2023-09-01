use std::fs::File;
use std::io::prelude::*;
use serde_json;

pub static GITHUB_API: &str = "https://api.github.com/search/repositories?q=topic:rust&per_page=100";    

pub struct Repository {
    pub name: String,
    pub description: String,
    pub url: String,
}

impl Repository {
    pub fn new(name: String, description: String, url: String) -> Repository {
        Repository {
            name,
            description,
            url
        }
    }
}

pub struct Response {
    pub total_count: u32,
    pub incomplete_results: bool,
    pub items: Vec<Repository>,
}

impl Response {
    pub fn new(total_count: u32, incomplete_results: bool, items: Vec<Repository>) -> Response {
        Response {
            total_count,
            incomplete_results,
            items,
        }
    }
}

fn main() {
    let mut file = File::create("README.md")
        .expect("Error encountered while creating file!");

    file.write(b"# Tools create in Rust\n\n")
        .expect("Error encountered while writing to file!");

    file.write(b"Parady to \"Everybody cares about random tools created in rust\".\n\n")
        .expect("Error encountered while writing to file!");

    let body = ureq::get(GITHUB_API)
        .call()
        .unwrap()
        .into_string();

    // Parse the response body as JSON.
    let json: serde_json::Value = serde_json::from_str(&body.unwrap()).unwrap();

    // Get the total count of repositories.
    let total_count = json["total_count"].as_u64().unwrap();

    file.write(b"Total repositories: ")
        .expect("Error encountered while writing to file!");
    file.write(total_count.to_string().as_bytes())
        .expect("Error encountered while writing to file!");
    file.write(b"\n\n")
        .expect("Error encountered while writing to file!");

    // Get the items array.
    let items = json["items"].as_array().unwrap();

    // Iterate over the items array.
    for item in items {
        // Get the name of the repository.
        let name = item["name"].as_str().unwrap();

        // Get the description of the repository.
        let description = item["description"].as_str().unwrap();

        // Get the url of the repository.
        let url = item["html_url"].as_str().unwrap();

        // Create a new repository.
        let repository = Repository::new(name.to_string(), description.to_string(), url.to_string());

        // Write the repository to the file.
        // Format: - [name](url) - description
        file.write(b"- [")
            .expect("Error encountered while writing to file!");
        file.write(repository.name.as_bytes())
            .expect("Error encountered while writing to file!");
        file.write(b"](")
            .expect("Error encountered while writing to file!");
        file.write(repository.url.as_bytes())
            .expect("Error encountered while writing to file!");
        file.write(b") - ")
            .expect("Error encountered while writing to file!");
        file.write(repository.description.as_bytes())
            .expect("Error encountered while writing to file!");
        file.write(b"\n")
            .expect("Error encountered while writing to file!");

    }

    file.write(b"\n\n")
        .expect("Error encountered while writing to file!");

    file.write(b"## License\n\n")
        .expect("Error encountered while writing to file!");
    file.write(b"This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details\n\n")
        .expect("Error encountered while writing to file!");

    file.write(b"## Acknowledgments\n\n")
        .expect("Error encountered while writing to file!");
    file.write(b"- [GitHub](https://github.com)\n")
        .expect("Error encountered while writing to file!");
    file.write(b"- [Rust](https://www.rust-lang.org)\n")
        .expect("Error encountered while writing to file!");

    file.write(b"\n\n")
        .expect("Error encountered while writing to file!");

    file.write(b"##### _Last Run on ")
        .expect("Error encountered while writing to file!");
    
    let now = chrono::Local::now()
        .format("%d-%m-%Y %H:%M:%S")
        .to_string();

    file.write(now.to_string().as_bytes())
        .expect("Error encountered while writing to file!");

    file.write(b"_\n\n")
        .expect("Error encountered while writing to file!");

    Ok::<(), ()>(())
        .expect("Error encountered while writing to file!");
}
