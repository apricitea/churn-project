import streamlit as st

st.write("## Meet Our Team")

stcol = st.columns(3)


def linkedin(username, only_html=False):
	platform = "linkedin"
	iconLink = "https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg"
	domain = "https://www.linkedin.com/in"
	body = f'[<img src="{iconLink}" alt="{platform}" width="25" width="auto"/>]({domain}/{username}/)'
	
	if only_html:
		return body
	else:
		return st.markdown(body, unsafe_allow_html=True)


def github(username, only_html=False):
	platform = "github"
	iconLink = "https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png"
	domain = "https://www.github.com"
	body = f'[<img src="{iconLink}" alt="{platform}" width="25" width="auto"/>]({domain}/{username}/)'

	if only_html:
		return body
	else:
		return st.markdown(body, unsafe_allow_html=True)

def socialMedia(usernameLinkedin, usernameGithub):
	return st.markdown(f"{linkedin(usernameLinkedin, True)} {github(usernameGithub, True)}", unsafe_allow_html=True)


with stcol[0]:
	st.image("https://media.licdn.com/dms/image/C5603AQEeBLh0IhMF-w/profile-displayphoto-shrink_800_800/0/1652586725629?e=1707350400&v=beta&t=01OmS-rT54taMv7YQcKGbBNL7SgPPVdpN5ClOOYqkvY")
	st.write("Alvin Christian N.")
	socialMedia("alvincnataputra", "apricitea")
	
with stcol[1]:
	st.image("https://media.licdn.com/dms/image/D5603AQFc7MC5HkZ5Ew/profile-displayphoto-shrink_800_800/0/1671193466047?e=1707350400&v=beta&t=8wurGVrjBxVAdF3fFQQ5Emy59ns6PKg7tVP8j4fGYUY")
	st.write("Muhammad Ammar S.")
	socialMedia("mammarstpc", "mammarstpc")

with stcol[2]:
	st.image("https://media.licdn.com/dms/image/C5603AQHPMw-uo0T14Q/profile-displayphoto-shrink_800_800/0/1659683923107?e=1707350400&v=beta&t=3dN3rtARbHbLKyrVpS_QGGpxdLveKTd6OCbjP3yfMCI")
	st.write("Perisai Zidane H.")
	#linkedin("pzidaneh")
	#github("pzidaneh")
	socialMedia("pzidaneh", "pzidaneh")
	
style = "<style>p {text-align: center;}</style>"
st.markdown(style, unsafe_allow_html=True)
