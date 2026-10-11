import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

class EmailAuthScreen extends StatefulWidget {
  const EmailAuthScreen({super.key});

  @override
  State<EmailAuthScreen> createState() => _EmailAuthScreenState();
}

class _EmailAuthScreenState extends State<EmailAuthScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _registerMode = false;
  bool _busy = false;
  bool _hidePassword = true;
  String? _error;
  String? _notice;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
    });
    try {
      final email = _emailController.text.trim();
      final password = _passwordController.text;
      if (_registerMode) {
        await FirebaseAuth.instance.createUserWithEmailAndPassword(
          email: email,
          password: password,
        );
      } else {
        await FirebaseAuth.instance.signInWithEmailAndPassword(
          email: email,
          password: password,
        );
      }
      // AuthGate observes authStateChanges and opens the dashboard.
    } on FirebaseAuthException catch (exception) {
      if (!mounted) return;
      setState(() => _error = _friendlyAuthError(exception.code));
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'Login nahi ho saka. Network check karke dobara try karein.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _sendPasswordReset() async {
    final email = _emailController.text.trim();
    if (email.isEmpty || !email.contains('@')) {
      setState(() => _error = 'Password reset ke liye pehle sahi email likhein.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
    });
    try {
      await FirebaseAuth.instance.sendPasswordResetEmail(email: email);
      if (mounted) {
        setState(() => _notice = 'Password reset email bhej diya gaya hai. Inbox check karein.');
      }
    } on FirebaseAuthException catch (exception) {
      if (mounted) setState(() => _error = _friendlyAuthError(exception.code));
    } catch (_) {
      if (mounted) setState(() => _error = 'Reset email nahi bheja ja saka. Dobara try karein.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  String _friendlyAuthError(String code) {
    switch (code) {
      case 'invalid-email':
        return 'Email address sahi format mein likhein.';
      case 'user-disabled':
        return 'Yeh account band hai. Administrator se sampark karein.';
      case 'user-not-found':
      case 'wrong-password':
      case 'invalid-credential':
        return 'Email ya password sahi nahi hai.';
      case 'email-already-in-use':
        return 'Is email se account pehle se bana hua hai. Login karein.';
      case 'weak-password':
        return 'Password kam se kam 6 characters ka rakhein.';
      case 'too-many-requests':
        return 'Bahut zyada koshish hui. Thodi der baad dobara try karein.';
      case 'operation-not-allowed':
        return 'Firebase Console mein Email/Password sign-in enable karein.';
      case 'network-request-failed':
        return 'Internet connection check karein.';
      default:
        return 'Authentication nahi ho saki ($code). Firebase settings check karein.';
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('AI-COMP account')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 460),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Icon(
                          Icons.school_outlined,
                          size: 48,
                          color: theme.colorScheme.primary,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          _registerMode ? 'नया account बनाएँ' : 'AI-COMP में Login करें',
                          style: theme.textTheme.headlineSmall,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _registerMode
                              ? 'अपनी तैयारी और progress के लिए account बनाएँ।'
                              : 'अपनी तैयारी जारी रखने के लिए email से login करें।',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 20),
                        TextFormField(
                          controller: _emailController,
                          keyboardType: TextInputType.emailAddress,
                          autocorrect: false,
                          autofillHints: const [AutofillHints.email],
                          decoration: const InputDecoration(
                            labelText: 'Email',
                            prefixIcon: Icon(Icons.email_outlined),
                          ),
                          validator: (value) {
                            final email = value?.trim() ?? '';
                            if (!email.contains('@') || email.endsWith('@')) {
                              return 'Valid email address लिखें।';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 12),
                        TextFormField(
                          controller: _passwordController,
                          obscureText: _hidePassword,
                          autocorrect: false,
                          enableSuggestions: false,
                          autofillHints: [
                            _registerMode ? AutofillHints.newPassword : AutofillHints.password,
                          ],
                          decoration: InputDecoration(
                            labelText: 'Password',
                            prefixIcon: const Icon(Icons.lock_outline),
                            suffixIcon: IconButton(
                              onPressed: () => setState(() => _hidePassword = !_hidePassword),
                              tooltip: _hidePassword ? 'Password dikhayein' : 'Password chhupayein',
                              icon: Icon(_hidePassword ? Icons.visibility : Icons.visibility_off),
                            ),
                          ),
                          validator: (value) {
                            final password = value ?? '';
                            if (password.length < 6) {
                              return 'Password कम से कम 6 characters का होना चाहिए।';
                            }
                            return null;
                          },
                        ),
                        if (!_registerMode) ...[
                          Align(
                            alignment: Alignment.centerRight,
                            child: TextButton(
                              onPressed: _busy ? null : _sendPasswordReset,
                              child: const Text('Password भूल गए?'),
                            ),
                          ),
                        ] else
                          const SizedBox(height: 12),
                        if (_error != null) ...[
                          Text(
                            _error!,
                            style: TextStyle(color: theme.colorScheme.error),
                          ),
                          const SizedBox(height: 8),
                        ],
                        if (_notice != null) ...[
                          Text(
                            _notice!,
                            style: TextStyle(color: theme.colorScheme.primary),
                          ),
                          const SizedBox(height: 8),
                        ],
                        FilledButton(
                          onPressed: _busy ? null : _submit,
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            child: _busy
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : Text(_registerMode ? 'Create account' : 'Login'),
                          ),
                        ),
                        const SizedBox(height: 8),
                        TextButton(
                          onPressed: _busy
                              ? null
                              : () => setState(() {
                                    _registerMode = !_registerMode;
                                    _error = null;
                                    _notice = null;
                                  }),
                          child: Text(
                            _registerMode
                                ? 'Pehle se account hai? Login karein'
                                : 'Naya account banana hai? Register karein',
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
