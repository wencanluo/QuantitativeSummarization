set cid=%1
set maxLecture=%2
for %%c in (%cid%) do (
	for /L %%w in (1, 1, %maxLecture%) do (
		for %%t in (q1 q2 q3 q4) do (
			rem if NOT exist "..\data\%%c\senna\senna.%%w.%%t.output" (
				if exist "..\data\%%c\senna\senna.%%w.%%t.input" (
					D:\NLP\senna\senna-win32.exe -path D:\NLP\senna\ < ..\data\%%c\senna\senna.%%w.%%t.input > ..\data\%%c\senna\senna.%%w.%%t.output
				)
			rem )
		)
	)
)