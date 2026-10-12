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
  final _confirmPasswordController = TextEditingController();

  bool _registerMode = false;
  bool _busy = false;
  bool _hidePassword = true;
  String? _error;
  String? _notice;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
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
        final credential = await FirebaseAuth.instance.createUserWithEmailAndPassword(
          email: email,
          password: password,
        );
        await credential.user?.sendEmailVerification();
        // The authentication gate keeps unverified users on EmailVerificationScreen.
      } else {
        final credential = await FirebaseAuth.instance.signInWithEmailAndPassword(
          email: email,
          password: password,
        );
        final user = credential.user;
        if (user != null && !user.emailVerified) {
          // Keep the user out of the dashboard and help them finish verification.
          await user.sendEmailVerification();
        }
        // Verified users enter the dashboard through the authentication gate.
      }
    } on FirebaseAuthException catch (exception) {
      if (!mounted) return;
      setState(() => _error = _friendlyAuthError(exception.code));
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'The request could not be completed. Check your internet connection and try again.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _sendPasswordReset() async {
    final email = _emailController.text.trim();
    if (email.isEmpty || !email.contains('@') || email.endsWith('@')) {
      setState(() => _error = 'Enter your email address first to receive a password reset link.');
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
        setState(() => _notice = 'A password reset link has been sent if this email is registered. Check your inbox and spam folder.');
      }
    } on FirebaseAuthException catch (exception) {
      if (mounted) setState(() => _error = _friendlyAuthError(exception.code));
    } catch (_) {
      if (mounted) setState(() => _error = 'The password reset email could not be sent. Please try again.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  String _friendlyAuthError(String code) {
    switch (code) {
      case 'invalid-email':
        return 'Enter a valid email address.';
      case 'user-disabled':
        return 'This account has been disabled. Contact the administrator.';
      case 'user-not-found':
      case 'wrong-password':
      case 'invalid-credential':
        return 'The email address or password is incorrect.';
      case 'email-already-in-use':
        return 'An account already exists for this email. Please sign in instead.';
      case 'weak-password':
        return 'Use a password with at least 6 characters.';
      case 'too-many-requests':
        return 'Too many attempts. Please wait a little and try again.';
      case 'operation-not-allowed':
        return 'Email/Password sign-in is disabled. Enable it in Firebase Console.';
      case 'network-request-failed':
        return 'No network connection. Check your internet and try again.';
      default:
        return 'Authentication failed ($code). Check your connection and Firebase settings.';
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
                          _registerMode ? 'Create your account' : 'Sign in to AI-COMP',
                          style: theme.textTheme.headlineSmall,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _registerMode
                              ? 'Create an account to save your preparation and progress.'
                              : 'Sign in to continue your exam preparation.',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 20),
                        TextFormField(
                          controller: _emailController,
                          keyboardType: TextInputType.emailAddress,
                          autocorrect: false,
                          autofillHints: const [AutofillHints.email],
                          decoration: const InputDecoration(
                            labelText: 'Email address',
                            prefixIcon: Icon(Icons.email_outlined),
                          ),
                          validator: (value) {
                            final email = value?.trim() ?? '';
                            if (!email.contains('@') || email.endsWith('@') || email.contains(' ')) {
                              return 'Enter a valid email address.';
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
                              tooltip: _hidePassword ? 'Show password' : 'Hide password',
                              icon: Icon(_hidePassword ? Icons.visibility : Icons.visibility_off),
                            ),
                          ),
                          validator: (value) {
                            final password = value ?? '';
                            if (password.length < 6) {
                              return 'Use at least 6 characters.';
                            }
                            return null;
                          },
                        ),
                        if (_registerMode) ...[
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: _confirmPasswordController,
                            obscureText: _hidePassword,
                            autocorrect: false,
                            enableSuggestions: false,
                            autofillHints: const [AutofillHints.newPassword],
                            decoration: const InputDecoration(
                              labelText: 'Confirm password',
                              prefixIcon: Icon(Icons.lock_reset_outlined),
                            ),
                            validator: (value) {
                              if (value != _passwordController.text) {
                                return 'Passwords do not match.';
                              }
                              return null;
                            },
                          ),
                          const SizedBox(height: 12),
                          Text(
                            'We will send an email verification link before you can sign in.',
                            style: theme.textTheme.bodySmall,
                          ),
                        ] else ...[
                          Align(
                            alignment: Alignment.centerRight,
                            child: TextButton(
                              onPressed: _busy ? null : _sendPasswordReset,
                              child: const Text('Forgot password?'),
                            ),
                          ),
                        ],
                        if (_error != null) ...[
                          Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
                          const SizedBox(height: 8),
                        ],
                        if (_notice != null) ...[
                          Text(_notice!, style: TextStyle(color: theme.colorScheme.primary)),
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
                                ? 'Already have an account? Login'
                                : 'New to AI-COMP? Create an account',
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
