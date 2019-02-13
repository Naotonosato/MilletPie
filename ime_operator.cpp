#include "stdafx.h"
#include <Windows.h>
#pragma comment(lib,"imm32.lib")
#include <imm.h>
#include <string>
#include <iostream>


using namespace std;


/*
I want to do like this.
char* msg = "\n\n";
return msg;

but due to constrains of ctypes I wrote
the following program.
(returning (char*)string.c_str())
*/


extern "C" __declspec(dllexport) char* getCandidate()
{
	HWND hWnd = GetActiveWindow();
	HIMC hImc = ImmGetContext(hWnd);
	DWORD dwSize = ImmGetCandidateListA(hImc,0,NULL,0);
	HGLOBAL hMem = GlobalAlloc(GHND,dwSize);
	
	if (hMem == NULL || dwSize == 0)
	{
		string msg = "\n\n";
		char *cmsg = (char*)msg.c_str();
		return cmsg;
	}
	LPCANDIDATELIST lpCandidate = LPCANDIDATELIST(GlobalLock(hMem));
	ImmGetCandidateListA(hImc, 0, lpCandidate, dwSize);

	string candidates;
	
	for (unsigned int i = 0; i < lpCandidate->dwCount; i++)
	{
		candidates += (char*)lpCandidate + lpCandidate->dwOffset[i];
		candidates += " ";
	}

	char* chrcandidates = (char*)candidates.c_str();

	ImmReleaseContext(hWnd, hImc);
	GlobalFree(hMem);
	return chrcandidates;
}

extern "C" __declspec(dllexport) int getIsOpenIME()
{
	HWND hWnd = GetActiveWindow();
	HIMC hImc = ImmGetContext(hWnd);
	return ImmGetOpenStatus(hImc) ? 1:0;
}

extern "C" __declspec(dllexport) char* getComposition()
{
	HWND hWnd = GetActiveWindow();
	HIMC hImc = ImmGetContext(hWnd);
	char compStr[1028];
	int size = ImmGetCompositionStringA(hImc, GCS_COMPSTR,NULL,0);
	
	if (size == 0)
	{
		string msg = "\n\n";
		char *cmsg = (char*)msg.c_str();
		return cmsg;
	}
	ImmGetCompositionStringA(hImc, GCS_COMPSTR, compStr, size);
	compStr[size] = '\0';
	ImmReleaseContext(hWnd, hImc);
	return compStr;
}

extern "C" __declspec(dllexport) char* getEnterdString()
{
	HWND hWnd = GetActiveWindow();
	HIMC hImc = ImmGetContext(hWnd);
	char compStr[1028];
	int size = ImmGetCompositionStringA(hImc, GCS_RESULTSTR, NULL, 0);
	if (size == 0)
	{
		string msg = "\n\n";
		char* cmsg = (char*)msg.c_str();
		return cmsg;
	}
	ImmGetCompositionStringA(hImc, GCS_RESULTSTR, compStr, size);
	compStr[size] = '\0';
	ImmReleaseContext(hWnd, hImc);
	return compStr;
}

extern "C" __declspec(dllexport) void setComposition(char* cmpStr)
{
	HWND hWnd = GetActiveWindow();
	HIMC hImc = ImmGetContext(hWnd);

	ImmSetCompositionStringA(hImc, SCS_SETSTR, cmpStr, sizeof(cmpStr), NULL, 0);
	
	ImmNotifyIME(hImc, NI_COMPOSITIONSTR, CPS_CONVERT, 0);
	
	ImmReleaseContext(hWnd, hImc);
}





