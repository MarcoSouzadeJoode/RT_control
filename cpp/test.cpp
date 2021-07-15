#include <iostream>
using namespace std;

int main() {
	cout << "Hello World!\n";
	cout << "Testing\n";

	int myNum = 10;
	double myDouble = 3.14159265;

	int limit;
	cin >> limit;
	while (myDouble <= limit) {
		// cout << myNum << endl;
		cout << myDouble << endl;
		
		myDouble++;
	}

	double PI = 3.14159265;
	PI += 10;

  return 0;
}
